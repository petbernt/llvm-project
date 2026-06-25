//===-- Unittests for strtol ----------------------------------------------===//
//
// Part of the LLVM Project, under the Apache License v2.0 with LLVM Exceptions.
// See https://llvm.org/LICENSE.txt for license information.
// SPDX-License-Identifier: Apache-2.0 WITH LLVM-exception
//
//===----------------------------------------------------------------------===//

#include "src/stdlib/strtol.h"

#include "test/UnitTest/Test.h"

#include "StrtolTest.h"

STRTOL_TEST(Strtol, LIBC_NAMESPACE::strtol)

// @verifies stdlib.strtol.B1
// @verifies stdlib.strtol.B3
TEST_F(LlvmLibcStrtolTest, ConvertsSubjectSequenceAndEndPointer) {
  char *str_end = nullptr;
  const char *input = "  -123xyz";

  ASSERT_EQ(LIBC_NAMESPACE::strtol(input, &str_end, 10), -123L);
  ASSERT_ERRNO_SUCCESS();
  EXPECT_EQ(str_end - input, ptrdiff_t(6));
}

// @verifies stdlib.strtol.B2
TEST_F(LlvmLibcStrtolTest, InfersBaseFromPrefixes) {
  char *str_end = nullptr;

  const char *decimal = "123tail";
  ASSERT_EQ(LIBC_NAMESPACE::strtol(decimal, &str_end, 0), 123L);
  ASSERT_ERRNO_SUCCESS();
  EXPECT_EQ(str_end - decimal, ptrdiff_t(3));

  const char *octal = "0123tail";
  ASSERT_EQ(LIBC_NAMESPACE::strtol(octal, &str_end, 0), 0123L);
  ASSERT_ERRNO_SUCCESS();
  EXPECT_EQ(str_end - octal, ptrdiff_t(4));

  const char *hexadecimal = "0x10tail";
  ASSERT_EQ(LIBC_NAMESPACE::strtol(hexadecimal, &str_end, 0), 16L);
  ASSERT_ERRNO_SUCCESS();
  EXPECT_EQ(str_end - hexadecimal, ptrdiff_t(4));

  const char *binary = "0b101tail";
  ASSERT_EQ(LIBC_NAMESPACE::strtol(binary, &str_end, 0), 5L);
  ASSERT_ERRNO_SUCCESS();
  EXPECT_EQ(str_end - binary, ptrdiff_t(5));
}

// @verifies stdlib.strtol.B4
TEST_F(LlvmLibcStrtolTest, ReportsNoConversion) {
  char *str_end = nullptr;
  const char *input = "word10";

  ASSERT_EQ(LIBC_NAMESPACE::strtol(input, &str_end, 10), 0L);
  ASSERT_ERRNO_SUCCESS();
  EXPECT_EQ(str_end - input, ptrdiff_t(0));
}

// @verifies stdlib.strtol.B5
TEST_F(LlvmLibcStrtolTest, ReportsRangeErrors) {
  char *str_end = nullptr;
  const long max_long = LIBC_NAMESPACE::cpp::numeric_limits<long>::max();
  const long min_long = LIBC_NAMESPACE::cpp::numeric_limits<long>::min();

  const char *too_large = "123456789012345678901";
  ASSERT_EQ(LIBC_NAMESPACE::strtol(too_large, &str_end, 10), max_long);
  ASSERT_ERRNO_EQ(ERANGE);
  EXPECT_EQ(str_end - too_large, ptrdiff_t(21));

  const char *too_small = "-123456789012345678901";
  ASSERT_EQ(LIBC_NAMESPACE::strtol(too_small, &str_end, 10), min_long);
  ASSERT_ERRNO_EQ(ERANGE);
  EXPECT_EQ(str_end - too_small, ptrdiff_t(22));
}

// @verifies stdlib.strtol.B6
// @verifies stdlib.strtol.B7
TEST_F(LlvmLibcStrtolTest, RejectsInvalidBase) {
  const char *input = "10";
  char *str_end = nullptr;

  ASSERT_EQ(LIBC_NAMESPACE::strtol(input, &str_end, 1), 0L);
  ASSERT_ERRNO_EQ(EINVAL);
  EXPECT_EQ(str_end, nullptr);
}
