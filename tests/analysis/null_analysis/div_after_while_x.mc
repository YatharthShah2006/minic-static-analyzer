// EXPECT: Division by zero

int main() {
    int x = 76 + 12 - 37;
    while (x) {
        x = 1;
    }
    int y;
    y = 10 / x;
    return y;
}
