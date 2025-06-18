#include <Windows.h>
#include <iostream>

int main(int argc, char* argv[])
{
    if (argc != 2)
    {
        std::cout << "Usage: " << argv[0] << " <PID>" << std::endl;
        return 1;
    }

    DWORD pid = atol(argv[1]);
    HANDLE hProcess = OpenProcess(PROCESS_ALL_ACCESS, FALSE, pid);

    if (hProcess == NULL)
    {
        std::cout << "Failed to open process. Error code: " << GetLastError() << std::endl;
        return 1;
    }

    if (!DebugBreakProcess(hProcess))
    {
        std::cout << "Failed to break into process. Error code: " << GetLastError() << std::endl;
        CloseHandle(hProcess);
        return 1;
    }

    CloseHandle(hProcess);
    return 0;
}