/**
 * dxgi.dll proxy — GPU name spoof to GTX 1050 Ti
 *
 * Compile:
 *   clang -shared -o dxgi.dll dxgi_proxy.c -O2 -s
 *
 * Place dxgi.dll next to game .exe, run game.
 * Game sees "NVIDIA GeForce GTX 1050 Ti" via DXGI.
 */
#include <windows.h>
#include <stdio.h>
#include <stdlib.h>

#define TARGET_GPU L"NVIDIA GeForce GTX 1050 Ti"

/* ================================================================
 *  Real dxgi function pointers
 * ================================================================ */
static HMODULE g_RealDll = NULL;

typedef HRESULT (WINAPI *PFN_CreateDXGIFactory)(REFIID, void **);
typedef HRESULT (WINAPI *PFN_CreateDXGIFactory1)(REFIID, void **);
typedef HRESULT (WINAPI *PFN_CreateDXGIFactory2)(UINT, REFIID, void **);
typedef HRESULT (WINAPI *PFN_DXGIDeclareAdapterRemovalSupport)(void);

static PFN_CreateDXGIFactory  pCreateDXGIFactory = NULL;
static PFN_CreateDXGIFactory1 pCreateDXGIFactory1 = NULL;
static PFN_CreateDXGIFactory2 pCreateDXGIFactory2 = NULL;
static PFN_DXGIDeclareAdapterRemovalSupport pDeclareRemoval = NULL;

static void load_real(void)
{
    if (g_RealDll) return;
    WCHAR path[MAX_PATH];
    GetSystemDirectoryW(path, MAX_PATH);
    lstrcatW(path, L"\\dxgi.dll");
    g_RealDll = LoadLibraryW(path);
    if (!g_RealDll) return;
    pCreateDXGIFactory  = (PFN_CreateDXGIFactory) GetProcAddress(g_RealDll, "CreateDXGIFactory");
    pCreateDXGIFactory1 = (PFN_CreateDXGIFactory1)GetProcAddress(g_RealDll, "CreateDXGIFactory1");
    pCreateDXGIFactory2 = (PFN_CreateDXGIFactory2)GetProcAddress(g_RealDll, "CreateDXGIFactory2");
    pDeclareRemoval     = (PFN_DXGIDeclareAdapterRemovalSupport)GetProcAddress(g_RealDll, "DXGIDeclareAdapterRemovalSupport");
}

/* ================================================================
 *  VTable hooking helpers
 * ================================================================ */

/* IDXGIAdapter vtable layout:
 * [0]=QueryInterface, [1]=AddRef, [2]=Release,
 * [3-6]=SetPrivateData/SetPrivateDataInterface/GetPrivateData/GetParent,
 * [7]=EnumOutputs, [8]=GetDesc, [9]=CheckInterfaceSupport */
#define ADAPTER_GETDESC_IDX 8

/* IDXGIFactory vtable layout:
 * [0]=QueryInterface, [1]=AddRef, [2]=Release,
 * [3-6]=... [7]=EnumAdapters */
#define FACTORY_ENUMADAPTERS_IDX 7

typedef HRESULT (STDMETHODCALLTYPE *PFN_GetDesc)(void *, DXGI_ADAPTER_DESC *);
typedef HRESULT (STDMETHODCALLTYPE *PFN_EnumAdapters)(void *, UINT, void **);

/* Save hooks for cleanup */
static PFN_GetDesc g_GetDesc_Original = NULL;
static PFN_EnumAdapters g_EnumAdapters_Original = NULL;
static void *g_hooked_adapter = NULL;
static void **g_hooked_vtable = NULL;

/* ---- Patched GetDesc ---- */
static HRESULT STDMETHODCALLTYPE GetDesc_Hook(void *this_, DXGI_ADAPTER_DESC *pDesc)
{
    HRESULT hr = g_GetDesc_Original(this_, pDesc);
    if (SUCCEEDED(hr) && pDesc)
    {
        wcscpy_s(pDesc->Description, 128, TARGET_GPU);
    }
    return hr;
}

/* ---- Patched EnumAdapters ---- */
static HRESULT STDMETHODCALLTYPE EnumAdapters_Hook(void *this_, UINT Adapter, void **ppAdapter)
{
    HRESULT hr = g_EnumAdapters_Original(this_, Adapter, ppAdapter);
    if (SUCCEEDED(hr) && ppAdapter && *ppAdapter && Adapter == 0)
    {
        /* Hook adapter vtable on first enum */
        if (!g_hooked_adapter)
        {
            void **vtable = *(void***)(*ppAdapter);
            DWORD oldProtect;

            /* Save original GetDesc */
            g_GetDesc_Original = (PFN_GetDesc)vtable[ADAPTER_GETDESC_IDX];

            /* Patch */
            VirtualProtect(&vtable[ADAPTER_GETDESC_IDX], sizeof(void*), PAGE_READWRITE, &oldProtect);
            vtable[ADAPTER_GETDESC_IDX] = GetDesc_Hook;
            VirtualProtect(&vtable[ADAPTER_GETDESC_IDX], sizeof(void*), oldProtect, &oldProtect);

            g_hooked_adapter = *ppAdapter;
            g_hooked_vtable = vtable;
        }
    }
    return hr;
}

/* ---- Hook factory vtable ---- */
static void hook_factory(void *factory)
{
    void **vtable = *(void***)factory;
    DWORD oldProtect;

    /* EnumAdapters is vtable[7] */
    g_EnumAdapters_Original = (PFN_EnumAdapters)vtable[FACTORY_ENUMADAPTERS_IDX];

    VirtualProtect(&vtable[FACTORY_ENUMADAPTERS_IDX], sizeof(void*), PAGE_READWRITE, &oldProtect);
    vtable[FACTORY_ENUMADAPTERS_IDX] = EnumAdapters_Hook;
    VirtualProtect(&vtable[FACTORY_ENUMADAPTERS_IDX], sizeof(void*), oldProtect, &oldProtect);
}

/* ================================================================
 *  Exported functions
 * ================================================================ */

HRESULT WINAPI CreateDXGIFactory(REFIID riid, void **ppFactory)
{
    load_real();
    if (!pCreateDXGIFactory) return E_FAIL;
    HRESULT hr = pCreateDXGIFactory(riid, ppFactory);
    if (SUCCEEDED(hr) && ppFactory && *ppFactory)
        hook_factory(*ppFactory);
    return hr;
}

HRESULT WINAPI CreateDXGIFactory1(REFIID riid, void **ppFactory)
{
    load_real();
    if (!pCreateDXGIFactory1) return E_FAIL;
    HRESULT hr = pCreateDXGIFactory1(riid, ppFactory);
    if (SUCCEEDED(hr) && ppFactory && *ppFactory)
        hook_factory(*ppFactory);
    return hr;
}

HRESULT WINAPI CreateDXGIFactory2(UINT Flags, REFIID riid, void **ppFactory)
{
    load_real();
    if (!pCreateDXGIFactory2) return E_FAIL;
    HRESULT hr = pCreateDXGIFactory2(Flags, riid, ppFactory);
    if (SUCCEEDED(hr) && ppFactory && *ppFactory)
        hook_factory(*ppFactory);
    return hr;
}

HRESULT WINAPI DXGIDeclareAdapterRemovalSupport(void)
{
    load_real();
    if (!pDeclareRemoval) return E_FAIL;
    return pDeclareRemoval();
}

/* ================================================================
 *  DllMain
 * ================================================================ */
BOOL WINAPI DllMain(HINSTANCE hinst, DWORD reason, LPVOID reserved)
{
    if (reason == DLL_PROCESS_ATTACH)
    {
        DisableThreadLibraryCalls(hinst);
        load_real();
    }
    return TRUE;
}
