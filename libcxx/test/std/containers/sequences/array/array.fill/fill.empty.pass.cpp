//===----------------------------------------------------------------------===//
//
// Part of the LLVM Project, under the Apache License v2.0 with LLVM Exceptions.
// See https://llvm.org/LICENSE.txt for license information.
// SPDX-License-Identifier: Apache-2.0 WITH LLVM-exception
//
//===----------------------------------------------------------------------===//

// UNSUPPORTED: c++03

// <array>
// constexpr void fill(const T& value); // constexpr since C++20

#include <array>
#include <cassert>

#include "test_macros.h"

struct AssignmentCounter {
  int* assignments;

  TEST_CONSTEXPR_CXX20 AssignmentCounter& operator=(const AssignmentCounter& other) {
    assignments = other.assignments;
    ++*assignments;
    return *this;
  }
};

TEST_CONSTEXPR_CXX20 bool test() {
  int assignments                        = 0;
  const AssignmentCounter value          = {&assignments};
  std::array<AssignmentCounter, 0> empty = {};
  empty.fill(value);
  // @verifies array.fill.B2
  assert(assignments == 0);

  // Confirm that the counter observes assignments to a non-empty array.
  std::array<AssignmentCounter, 1> non_empty = {{{&assignments}}};
  non_empty.fill(value);
  assert(assignments == 1);
  return true;
}

int main(int, char**) {
  test();
#if TEST_STD_VER >= 20
  static_assert(test(), "");
#endif
  return 0;
}
