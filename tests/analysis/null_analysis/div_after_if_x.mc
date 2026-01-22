// EXPECT: Division by zero

int main() {
    int x;
    x = 10 - 10;
    if (x) {
        x = 5;
    }
    int y;
    y = 10 / x;
    print(y);
    return 0;
}
