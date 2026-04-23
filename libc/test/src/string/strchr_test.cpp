//===-- Unittests for strchr ----------------------------------------------===//
//
// Part of the LLVM Project, under the Apache License v2.0 with LLVM Exceptions.
// See https://llvm.org/LICENSE.txt for license information.
// SPDX-License-Identifier: Apache-2.0 WITH LLVM-exception
//
//===----------------------------------------------------------------------===//

#include "StrchrTest.h"

#include "src/string/strchr.h"
#include "test/UnitTest/Test.h"

using LlvmLibcStrchrTest = StrchrTest<LIBC_NAMESPACE::strchr>;

// @verifies string.strchr.B1
TEST_F(LlvmLibcStrchrTest, FindsFirstCharacter) { findsFirstCharacter(); }

TEST_F(LlvmLibcStrchrTest, FindsMiddleCharacter) { findsMiddleCharacter(); }

TEST_F(LlvmLibcStrchrTest, FindsLastCharacterThatIsNotNullTerminator) {
  findsLastCharacterThatIsNotNullTerminator();
}

// @verifies string.strchr.B2
TEST_F(LlvmLibcStrchrTest, FindsNullTerminator) { findsNullTerminator(); }

// @verifies string.strchr.B3
TEST_F(LlvmLibcStrchrTest, CharacterNotWithinStringShouldReturnNullptr) {
  characterNotWithinStringShouldReturnNullptr();
}

TEST_F(LlvmLibcStrchrTest, TheSourceShouldNotChange) { theSourceShouldNotChange(); }

TEST_F(LlvmLibcStrchrTest, ShouldFindFirstOfDuplicates) {
  shouldFindFirstOfDuplicates();
}

TEST_F(LlvmLibcStrchrTest, EmptyStringShouldOnlyMatchNullTerminator) {
  emptyStringShouldOnlyMatchNullTerminator();
}
