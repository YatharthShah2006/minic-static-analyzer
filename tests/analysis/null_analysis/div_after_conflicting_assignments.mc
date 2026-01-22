// EXPECT: Division by zero

int main() {
    int x;
    x = 15 - 10;
    if (x) {
        x = 1;
    } else {
        x = 0;
    }
    int y;
    y = 10 / x;
    return y;
}
