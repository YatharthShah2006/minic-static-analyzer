// EXPECT: Arithmetic operator '+' requires int operands

int main() {
    int x = 1209;
    x = (x < 3) + 1;
    return x;
}
