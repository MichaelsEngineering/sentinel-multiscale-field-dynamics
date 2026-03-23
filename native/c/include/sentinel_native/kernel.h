#ifndef SENTINEL_NATIVE_KERNEL_H
#define SENTINEL_NATIVE_KERNEL_H

#include <stddef.h>

#ifdef __cplusplus
extern "C" {
#endif

typedef struct sentinel_kernel_result {
    double max_abs;
    size_t element_count;
} sentinel_kernel_result;

sentinel_kernel_result sentinel_threaded_stencil_step(
    const double *input,
    double *output,
    size_t width,
    size_t height,
    double viscosity
);

#ifdef __cplusplus
}
#endif

#endif
