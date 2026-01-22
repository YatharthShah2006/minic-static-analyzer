// EXPECT: OK

int main() {
    int x;
    x = 3;
    while (x) {
        x = x - 1;
    }
    return x;
}
