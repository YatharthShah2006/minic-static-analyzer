// EXPECT: Dead store

int main() {
    int x;
    x = 3;
    x = 4;
    return x;
}
