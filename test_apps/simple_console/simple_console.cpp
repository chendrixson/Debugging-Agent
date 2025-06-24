#include <iostream>
#include <stdexcept>
#include <Windows.h>

// Null pointer dereference
void nullPointerDereference() {
    int* ptr = nullptr;
    std::cout << "Attempting to dereference null pointer..." << std::endl;
    std::cout << *ptr << std::endl;
}

// Division by zero
void divisionByZero() {
    int x = 5;
    int y = 0;
    std::cout << "Attempting to divide by zero..." << std::endl;
    std::cout << x / y << std::endl;
}

// Invalid array access
void invalidArrayAccess() {
    int arr[5] = { 1, 2, 3, 4, 5 };
    std::cout << "Attempting to access array out of bounds..." << std::endl;
    std::cout << arr[10] << std::endl;
}

// Medium complexity function
int calculateStatistics(int numbers[], int size) {
    int sum = 0;
    int min = numbers[0];
    int max = numbers[0];

    for (int i = 0; i < size; i++) {
        sum += numbers[i];

        if (numbers[i] < min) {
            min = numbers[i];
        }

        if (numbers[i] > max) {
            max = numbers[i];
        }
    }

    double average = static_cast<double>(sum) / size;

    std::cout << "Sum: " << sum << std::endl;
    std::cout << "Min: " << min << std::endl;
    std::cout << "Max: " << max << std::endl;
    std::cout << "Average: " << average << std::endl;

    return sum;
}

void printMenu() {
    std::cout << "Test App Menu:" << std::endl;
    std::cout << "1. Null Pointer Dereference" << std::endl;
    std::cout << "2. Division by Zero" << std::endl;
    std::cout << "3. Invalid Array Access" << std::endl;
    std::cout << "4. Calculate Statistics" << std::endl;
    std::cout << "5. Exit" << std::endl;
}

// Test mode for the automated tool test
void runTestMode()
{
    OutputDebugString(L"Running automated test mode, waiting for 5s then starting.");
    Sleep(5000);

    int numbers[] = { 40, 74, 129 };
    int size = sizeof(numbers) / sizeof(numbers[0]);

    // Test should be attached to the below function, then will walk through it
    calculateStatistics(numbers, size);

    Sleep(2000);
    
    // And then crash
    nullPointerDereference();
}

int main(int argc, char* argv[]) {
    // See if this is in test mode
    if (argc == 2 && !strcmp(argv[1], "test"))
    {
        runTestMode();
        return 1;
    }

    int choice;
    int numbers[] = { 1, 2, 3, 4, 5 };
    int size = sizeof(numbers) / sizeof(numbers[0]);

    while (true) {
        printMenu();
        std::cout << "Enter your choice: ";
        std::cin >> choice;

        switch (choice) {
        case 1:
            nullPointerDereference();
            break;
        case 2:
            divisionByZero();
            break;
        case 3:
            invalidArrayAccess();
            break;
        case 4:
            calculateStatistics(numbers, size);
            break;
        case 5:
            return 0;
        default:
            std::cout << "Invalid choice. Please try again." << std::endl;
        }

        std::cout << std::endl;
    }

    return 0;
}