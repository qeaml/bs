#include <stdio.h>

int rng();
const char *sub();

int main(int argc, char *argv[]) {
  printf("Hello world!\n");
  printf("RNG says %d!\n", rng());
  printf("%s\n", sub());
}
