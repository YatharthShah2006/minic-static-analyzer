// EXPECT: May not return

int f() {
    if (1) {
        return 3;
    }
}

int main() {
    return 0;
}
