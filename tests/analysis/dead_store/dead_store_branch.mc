// EXPECT: Dead store

int main() {
    int x;
    if (1) {
        x = 3;
    } else {
        x = 4;
    }
    x = 5;
    return x;
}
