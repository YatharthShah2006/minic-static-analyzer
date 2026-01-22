// EXPECT: Return type mismatch

int f() {
    return 3 < 4;
}

int main() {
    return f();
}
