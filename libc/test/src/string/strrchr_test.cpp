//===-- Unittests for strrchr ---------------------------------------------===//
//
// Part of the LLVM Project, under the Apache License v2.0 with LLVM Exceptions.
// See https://llvm.org/LICENSE.txt for license information.
// SPDX-License-Identifier: Apache-2.0 WITH LLVM-exception
//
//===----------------------------------------------------------------------===//

#include "StrchrTest.h"

#include "src/string/strrchr.h"
#include "test/UnitTest/Test.h"

using LlvmLibcStrrchrTest = StrrchrTest<LIBC_NAMESPACE::strrchr>;

// @verifies string.strrchr.B1
TEST_F(LlvmLibcStrrchrTest, FindsFirstCharacter) { findsFirstCharacter(); }

TEST_F(LlvmLibcStrrchrTest, FindsMiddleCharacter) { findsMiddleCharacter(); }

TEST_F(LlvmLibcStrrchrTest, FindsLastCharacterThatIsNotNullTerminator) {
  findsLastCharacterThatIsNotNullTerminator();
}

// @verifies string.strrchr.B2
TEST_F(LlvmLibcStrrchrTest, FindsNullTerminator) { findsNullTerminator(); }

TEST_F(LlvmLibcStrrchrTest, FindsLastBehindFirstNullTerminator) {
  findsLastBehindFirstNullTerminator();
}

// @verifies string.strrchr.B3
TEST_F(LlvmLibcStrrchrTest, CharacterNotWithinStringShouldReturnNullptr) {
  characterNotWithinStringShouldReturnNullptr();
}

TEST_F(LlvmLibcStrrchrTest, ShouldFindLastOfDuplicates) {
  shouldFindLastOfDuplicates();
}

TEST_F(LlvmLibcStrrchrTest, EmptyStringShouldOnlyMatchNullTerminator) {
  emptyStringShouldOnlyMatchNullTerminator();
}
