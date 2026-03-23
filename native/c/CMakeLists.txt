cmake_minimum_required(VERSION 3.25)
project(sentinel_native C)

add_library(sentinel_native STATIC src/threaded_stencil.c)
target_include_directories(sentinel_native PUBLIC include)

enable_testing()
add_executable(sentinel_native_smoke tests/test_threaded_stencil.c)
target_link_libraries(sentinel_native_smoke PRIVATE sentinel_native)
add_test(NAME sentinel_native_smoke COMMAND sentinel_native_smoke)
