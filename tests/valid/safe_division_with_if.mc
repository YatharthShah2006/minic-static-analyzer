// EXPECT: OK

int main() {
    int x;
    x = 15 - 78 * 125 + (36 / 5 * 12);
    if (x) {
        int y;
        y = 10 / x;
        print(y);
    }
    int y;
    y = 2 * x;
    return y;
}
