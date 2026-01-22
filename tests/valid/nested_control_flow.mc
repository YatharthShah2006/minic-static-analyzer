// EXPECT: OK

int main() {
    int x;
    x = 2;
    while (x) {
        if (x) {
            x = x - 1;
        } else {
            x = 1;
        }
    }
    return x;
}
