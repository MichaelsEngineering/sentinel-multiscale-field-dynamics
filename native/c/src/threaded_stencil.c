#include "sentinel_native/kernel.h"

#include <math.h>
#include <stddef.h>

sentinel_kernel_result sentinel_threaded_stencil_step(
    const double *input,
    double *output,
    size_t width,
    size_t height,
    double viscosity
) {
    sentinel_kernel_result result = {0.0, width * height};
    size_t total = width * height;
    for (size_t index = 0; index < total; ++index) {
        output[index] = input[index] * (1.0 - viscosity);
        double magnitude = fabs(output[index]);
        if (magnitude > result.max_abs) {
            result.max_abs = magnitude;
        }
    }
    return result;
}
