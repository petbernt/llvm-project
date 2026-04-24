add_subdirectory(hdrgen)

if(LLVM_LIBC_INCLUDE_BEHAVIOR_MAPPING)
  enable_testing()

  add_test(
    NAME libc_behavior_mapping_check_unit_test
    COMMAND python3 ${CMAKE_CURRENT_SOURCE_DIR}/behavior/tests/check_test.py
  )

  add_test(
    NAME libc_behavior_mapping_check
    COMMAND python3 ${CMAKE_CURRENT_SOURCE_DIR}/behavior/check.py --libc-dir
            ${CMAKE_CURRENT_SOURCE_DIR}/..
  )

  add_test(
    NAME libc_behavior_mapping_report_unit_test
    COMMAND python3 ${CMAKE_CURRENT_SOURCE_DIR}/behavior/tests/report_test.py
  )

  add_custom_target(check-libc-behavior-mapping
    COMMAND ${CMAKE_CTEST_COMMAND} -R libc_behavior_mapping_ --output-on-failure
  )

  add_custom_target(report-libc-behavior-mapping
    COMMAND python3 ${CMAKE_CURRENT_SOURCE_DIR}/behavior/report.py --libc-dir
            ${CMAKE_CURRENT_SOURCE_DIR}/.. --build-dir ${CMAKE_BINARY_DIR}
  )

  message(STATUS "Behavior mapping checks added.")
endif()

if(LLVM_INCLUDE_TESTS)
  add_subdirectory(MPFRWrapper)
  add_subdirectory(MPCWrapper)
endif()
