/**
 * dinput8.dll proxy — GPU name spoof to GTX 1050 Ti
 *
 * Compile (LLVM MinGW):
 *   clang -shared -o dinput8.dll dinput8_proxy.c -O2 -s -lole32
 *
 * Place dinput8.dll next to game .exe, run game.
 * DXGI will report "NVIDIA GeForce GTX 1050 Ti".
 */
#include <windows.h>
#include <stdio.h>

#define TARGET_GPU L"NVIDIA GeForce GTX 1050 Ti"

/* Manual DXGI_ADAPTER_DESC definition (avoid dxgi.h dependency) */
typedef struct {
    WCHAR  Description[128];
    UINT   VendorId;
    UINT   DeviceId;
    UINT   SubSysId;
    UINT   Revision;
    SIZE_T DedicatedVideoMemory;
    SIZE_T DedicatedSystemMemory;
    SIZE_T SharedSystemMemory;
    LUID   AdapterLuid;
} DXGI_ADAPTER_DESC;

/* ================================================================
 *  Real dinput8 forwarding
 * ================================================================ */
static HMODULE g_RealDinput8 = NULL;

typedef HRESULT (WINAPI *PFN_DirectInput8Create)(HINSTANCE, DWORD, REFIID, LPVOID *, LPUNKNOWN);

static PFN_DirectInput8Create pDirectInput8Create = NULL;

static void load_real_dinput8(void)
{
    if (g_RealDinput8) return;
    WCHAR path[MAX_PATH];
    GetSystemDirectoryW(path, MAX_PATH);
    lstrcatW(path, L"\\dinput8.dll");
    g_RealDinput8 = LoadLibraryW(path);
    if (g_RealDinput8)
        pDirectInput8Create = (PFN_DirectInput8Create)
            GetProcAddress(g_RealDinput8, "DirectInput8Create");
}

/* ================================================================
 *  DXGI vtable hooking
 * ================================================================ */
#define ADAPTER_GETDESC_IDX       8
#define FACTORY_ENUMADAPTERS_IDX  7

typedef HRESULT (WINAPI *PFN_CreateDXGIFactory1)(REFIID, void **);

typedef HRESULT (__stdcall *PFN_GetDesc)(void *, DXGI_ADAPTER_DESC *);
typedef HRESULT (__stdcall *PFN_EnumAdapters)(void *, UINT, void **);

/* COM base helpers — lpVtbl points to array of function ptrs */
typedef struct { void **lpVtbl; } IUnknownCom;
typedef ULONG (__stdcall *PFN_Release)(IUnknownCom *);

static PFN_GetDesc       g_OriginalGetDesc       = NULL;
static PFN_EnumAdapters  g_OriginalEnumAdapters  = NULL;
static int               g_DXGIPatched           = 0;

/* Patched GetDesc — replaces GPU name */
static HRESULT __stdcall GetDesc_Hook(void *this_, DXGI_ADAPTER_DESC *pDesc)
{
    HRESULT hr = g_OriginalGetDesc(this_, pDesc);
    if (SUCCEEDED(hr) && pDesc)
    {
        /* IDXGIAdapter::GetDesc vtable[8] */
        lstrcpyW(pDesc->Description, TARGET_GPU);
    }
    return hr;
}

/* Patched EnumAdapters — hooks adapter vtable on first call */
static HRESULT __stdcall EnumAdapters_Hook(void *this_, UINT Adapter, void **ppAdapter)
{
    HRESULT hr = g_OriginalEnumAdapters(this_, Adapter, ppAdapter);
    if (SUCCEEDED(hr) && ppAdapter && *ppAdapter && Adapter == 0)
    {
        /* On first adapter, patch its GetDesc */
        void **vtable = *(void ***)(*ppAdapter);
        if (vtable && !g_OriginalGetDesc)
        {
            DWORD oldProtect;
            g_OriginalGetDesc = (PFN_GetDesc)vtable[ADAPTER_GETDESC_IDX];
            VirtualProtect(&vtable[ADAPTER_GETDESC_IDX], sizeof(void *),
                           PAGE_EXECUTE_READWRITE, &oldProtect);
            vtable[ADAPTER_GETDESC_IDX] = GetDesc_Hook;
            VirtualProtect(&vtable[ADAPTER_GETDESC_IDX], sizeof(void *),
                           oldProtect, &oldProtect);
        }
    }
    return hr;
}

static void try_patch_dxgi(void)
{
    if (g_DXGIPatched) return;

    HMODULE dxgi = GetModuleHandleW(L"dxgi.dll");
    if (!dxgi) dxgi = LoadLibraryW(L"dxgi.dll");
    if (!dxgi) return;

    PFN_CreateDXGIFactory1 pCreate = (PFN_CreateDXGIFactory1)
        GetProcAddress(dxgi, "CreateDXGIFactory1");
    if (!pCreate) return;

    /* IID_IDXGIFactory1 = {770AAE78-F26F-4DBA-A829-253C83D1B387} */
    GUID iid;
    iid.Data1 = 0x770AAE78;
    iid.Data2 = 0xF26F;
    iid.Data3 = 0x4DBA;
    iid.Data4[0] = 0xA8; iid.Data4[1] = 0x29;
    iid.Data4[2] = 0x25; iid.Data4[3] = 0x3C;
    iid.Data4[4] = 0x83; iid.Data4[5] = 0xD1;
    iid.Data4[6] = 0xB3; iid.Data4[7] = 0x87;

    IUnknownCom *factory = NULL;
    HRESULT hr = pCreate(&iid, (void**)&factory);
    if (FAILED(hr) || !factory) return;

    void **vtable = factory->lpVtbl;
    if (!vtable)
    {
        /* Release via vtable[2] */
        PFN_Release release = (PFN_Release)vtable[2];
        if (release) release(factory);
        return;
    }

    DWORD oldProtect;
    g_OriginalEnumAdapters = (PFN_EnumAdapters)vtable[FACTORY_ENUMADAPTERS_IDX];
    VirtualProtect(&vtable[FACTORY_ENUMADAPTERS_IDX], sizeof(void *),
                   PAGE_EXECUTE_READWRITE, &oldProtect);
    vtable[FACTORY_ENUMADAPTERS_IDX] = EnumAdapters_Hook;
    VirtualProtect(&vtable[FACTORY_ENUMADAPTERS_IDX], sizeof(void *),
                   oldProtect, &oldProtect);

    /* Release factory */
    PFN_Release release = (PFN_Release)vtable[2];
    release(factory);
    g_DXGIPatched = 1;
}

/* ================================================================
 *  Exports — dinput8.dll
 * ================================================================ */

HRESULT WINAPI DirectInput8Create(HINSTANCE hinst, DWORD dwVersion,
                                   REFIID riidltf, LPVOID *ppvOut, LPUNKNOWN punkOuter)
{
    load_real_dinput8();
    if (!pDirectInput8Create) return E_FAIL;
    /* Defer patching to first dinput call (safe, COM initialized) */
    try_patch_dxgi();
    return pDirectInput8Create(hinst, dwVersion, riidltf, ppvOut, punkOuter);
}

HRESULT WINAPI DllCanUnloadNow(void)  { return S_FALSE; }

HRESULT WINAPI DllGetClassObject(REFCLSID rclsid, REFIID riid, LPVOID *ppv)
{
    load_real_dinput8();
    typedef HRESULT (WINAPI *PFN)(REFCLSID, REFIID, LPVOID *);
    PFN fn = (PFN)GetProcAddress(g_RealDinput8, "DllGetClassObject");
    return fn ? fn(rclsid, riid, ppv) : E_FAIL;
}

HRESULT WINAPI DllRegisterServer(void)
{
    load_real_dinput8();
    typedef HRESULT (WINAPI *PFN)(void);
    PFN fn = (PFN)GetProcAddress(g_RealDinput8, "DllRegisterServer");
    return fn ? fn() : E_FAIL;
}

HRESULT WINAPI DllUnregisterServer(void)
{
    load_real_dinput8();
    typedef HRESULT (WINAPI *PFN)(void);
    PFN fn = (PFN)GetProcAddress(g_RealDinput8, "DllUnregisterServer");
    return fn ? fn() : E_FAIL;
}

/* ================================================================
 *  DllMain
 * ================================================================ */
BOOL WINAPI DllMain(HINSTANCE hinst, DWORD reason, LPVOID reserved)
{
    if (reason == DLL_PROCESS_ATTACH)
    {
        DisableThreadLibraryCalls(hinst);
        load_real_dinput8();
    }
    return TRUE;
}
