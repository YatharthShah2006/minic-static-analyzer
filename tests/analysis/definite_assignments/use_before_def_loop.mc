// EXPECT: Unassigned

int main() {
    int x;
    while (0) {
        x = 3;
    }
    return x;
}
