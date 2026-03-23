#include "sentinel_native/kernel.h"

#include <stdio.h>

int main(void) {
    double input[4] = {1.0, -2.0, 3.0, -4.0};
    double output[4] = {0.0, 0.0, 0.0, 0.0};
    sentinel_kernel_result result = sentinel_threaded_stencil_step(input, output, 2, 2, 0.1);
    if (result.element_count != 4) {
        return 1;
    }
    if (output[0] <= 0.0 || output[3] >= 0.0) {
        return 2;
    }
    puts("sentinel_native_smoke_ok");
    return 0;
}
