//===-- Unittests for strlen ----------------------------------------------===//
//
// Part of the LLVM Project, under the Apache License v2.0 with LLVM Exceptions.
// See https://llvm.org/LICENSE.txt for license information.
// SPDX-License-Identifier: Apache-2.0 WITH LLVM-exception
//
//===----------------------------------------------------------------------===//

#include "src/string/strlen.h"
#include "hdr/signal_macros.h"
#include "test/UnitTest/Test.h"

// @verifies string.strlen.B1
TEST(LlvmLibcStrLenTest, EmptyString) {
  const char *empty = "";

  size_t result = LIBC_NAMESPACE::strlen(empty);
  ASSERT_EQ((size_t)0, result);
}

// @verifies string.strlen.B2
TEST(LlvmLibcStrLenTest, AnyString) {
  const char *any = "Hello World!";

  size_t result = LIBC_NAMESPACE::strlen(any);
  ASSERT_EQ((size_t)12, result);
}

// @verifies string.strlen.B3
TEST(LlvmLibcStrLenTest, DataAfterNulString) {
  constexpr char A[10] = {'a', 'b', 'c', 'd', 'e', 'f', 0, 'h', 'i', 'j'};
  size_t result = LIBC_NAMESPACE::strlen(A);
  ASSERT_EQ((size_t)6, result);
}

TEST(LlvmLibcStrLenTest, MultipleNulsInOneWord) {
  constexpr char A[10] = {'a', 'b', 0, 'd', 'e', 'f', 0, 'h', 'i', 'j'};
  size_t result = LIBC_NAMESPACE::strlen(A);
  ASSERT_EQ((size_t)2, result);
}

#if defined(LIBC_ADD_NULL_CHECKS)

// @verifies string.strlen.B4
TEST(LlvmLibcStrLenTest, CrashOnNullPtr) {
  ASSERT_DEATH([]() { (void)LIBC_NAMESPACE::strlen(nullptr); }, WITH_SIGNAL(-1));
}

#endif // defined(LIBC_ADD_NULL_CHECKS)
