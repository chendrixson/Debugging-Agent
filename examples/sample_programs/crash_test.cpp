// Simple C++ program that crashes for testing the debugger
#include <iostream>

void cause_access_violation() {
    int* null_ptr = nullptr;
    *null_ptr = 42;  // This will cause an access violation
}

void cause_stack_overflow() {
    cause_stack_overflow();  // Infinite recursion
}

void cause_division_by_zero() {
    int x = 10;
    int y = 0;
    int result = x / y;  // Division by zero
    std::cout << "Result: " << result << std::endl;
}

int main(int argc, char* argv[]) {
    std::cout << "Crash Test Program" << std::endl;
    std::cout << "Choose crash type:" << std::endl;
    std::cout << "1. Access Violation" << std::endl;
    std::cout << "2. Stack Overflow" << std::endl;
    std::cout << "3. Division by Zero" << std::endl;
    
    int choice = 1;
    if (argc > 1) {
        choice = std::atoi(argv[1]);
    }
    
    std::cout << "Triggering crash type " << choice << "..." << std::endl;
    
    switch (choice) {
        case 1:
            cause_access_violation();
            break;
        case 2:
            cause_stack_overflow();
            break;
        case 3:
            cause_division_by_zero();
            break;
        default:
            std::cout << "Invalid choice, defaulting to access violation" << std::endl;
            cause_access_violation();
            break;
    }
    
    std::cout << "This line should not be reached" << std::endl;
    return 0;
} 