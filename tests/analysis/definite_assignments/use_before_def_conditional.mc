// EXPECT: Unassigned

int main() {
    int x;
    if (1) {
        x = 3;
    }
    return x;
}
