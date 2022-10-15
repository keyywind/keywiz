#include <bits/stdc++.h>

#include "utils.hpp"

extern "C"
{
    void find_optimal_move(int * sr, int * sc, int * er, int * ec, int board[PotionUtils::rows * PotionUtils::cols])
    {
        int A[PotionUtils::rows][PotionUtils::cols];  memcpy(A, board, PotionUtils::rows * PotionUtils::cols * sizeof(int));
        PotionUtils::PotionCoord potionCoord = PotionUtils::find_optimal_move(A);
        *sr = potionCoord.sr();
        *sc = potionCoord.sc();
        *er = potionCoord.er();
        *ec = potionCoord.ec();
    }
}

int main()
{
    using PotionCoord = PotionUtils::PotionCoord;

    int A[PotionUtils::rows][PotionUtils::cols] = {
        {  0, 0, 1, 1, 2, 2, 3  },
        {  3, 3, 2, 2, 1, 1, 3  },
        {  0, 0, 1, 4, 2, 2, 4  },
        {  1, 0, 3, 1, 2, 2, 3  },
        {  0, 1, 1, 2, 1, 1, 2  },
        {  1, 0, 2, 3, 3, 2, 3  }
    };

    PotionUtils::print_board(A);

    PotionCoord potionCoord = PotionUtils::find_optimal_move(A);

    int sc = potionCoord.sc(),
        sr = potionCoord.sr(),
        ec = potionCoord.ec(),
        er = potionCoord.er();

    printf("(%d, %d, %d, %d)\n\n", sr, sc, er, ec);

    int I, J, K;

    PotionUtils::SE2IJK(I, J, K, sc, sr, ec, er);

    PotionUtils::shift_board_basic(A, I, J, K);

    PotionUtils::print_board(A);

    return 0;
}
