// EXPECT: Argument type mismatch

int f(int x) {
    return x;
}

int main() {
    return f(3 < 4);
}
