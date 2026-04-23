add_subdirectory(hdrgen)

if(LLVM_LIBC_FULL_BUILD)
  enable_testing()

  add_test(
    NAME libc_behavior_mapping_check_unit_test
    COMMAND python3 ${CMAKE_CURRENT_SOURCE_DIR}/behavior_mapping_check_test.py
  )

  add_test(
    NAME libc_behavior_mapping_check
    COMMAND python3 ${CMAKE_CURRENT_SOURCE_DIR}/behavior_mapping_check.py --libc-dir
            ${CMAKE_CURRENT_SOURCE_DIR}/..
  )

  add_custom_target(check-libc-behavior-mapping
    COMMAND ${CMAKE_CTEST_COMMAND} -R libc_behavior_mapping_ --output-on-failure
  )

  message(STATUS "Behavior mapping checks added.")
endif()

if(LLVM_INCLUDE_TESTS)
  add_subdirectory(MPFRWrapper)
  add_subdirectory(MPCWrapper)
endif()
