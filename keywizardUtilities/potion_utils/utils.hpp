#ifndef H_POTION_UTILS
#define H_POTION_UTILS

namespace PotionUtils
{

    class PotionCoord
    {
    private:
        int SC, SR, EC, ER;
    public:
        PotionCoord(int sc, int sr, int ec, int er) : SC(sc), SR(sr), EC(ec), ER(er) {  ;  }
        int & sc() {  return SC;  }
        int & sr() {  return SR;  }
        int & ec() {  return EC;  }
        int & er() {  return ER;  }
    };

    static const int rows   = 6,
                     cols   = 7,
                     height = 8,
                     width  = 9;

    static const int boundary_matrix[height][width] = {
        {  0, 0, 0, 0, 0, 0, 0, 0, 0  },
        {  0, 1, 1, 1, 1, 1, 1, 1, 0  },
        {  0, 1, 1, 1, 1, 1, 1, 1, 0  },
        {  0, 1, 1, 1, 1, 1, 1, 1, 0  },
        {  0, 1, 1, 1, 1, 1, 1, 1, 0  },
        {  0, 1, 1, 1, 1, 1, 1, 1, 0  },
        {  0, 1, 1, 1, 1, 1, 1, 1, 0  },
        {  0, 0, 0, 0, 0, 0, 0, 0, 0  }
    };

    int depth_first_search(int A[height][width], int B[height][width], int R, int I, int J)
    {
        if ((B[I][J]) && (A[I][J] == R))
        {
            B[I][J] = 0;
            return 1 + depth_first_search(A, B, R, I - 1, J)
                     + depth_first_search(A, B, R, I + 1, J)
                     + depth_first_search(A, B, R, I, J - 1)
                     + depth_first_search(A, B, R, I, J + 1);
        }
        return 0;
    }

    int compute_score(int n)
    {
        if (n < 3)
        {
            return 0;
        }
        switch (n)
        {
        case (3):
            return 30;
        case (4):
            return 60;
        case (5):
            return 100;
        default:
            return compute_score(n - 1) + 10 * (n - 1);
        }
    }

    int evaluate_board(int A[height][width])
    {
        int B[height][width];  memcpy(B, boundary_matrix, height * width * sizeof(int));
        int score = 0;
        for (int i = 1, boundI = i + rows; i < boundI; ++i)
        {
            for (int j = 1, boundJ = j + cols; j < boundJ; ++j)
            {
                if (B[i][j])
                {
                    score += compute_score(depth_first_search(A, B, A[i][j], i, j));
                }
            }
        }
        return score;
    }

    void shift_board(int A[height][width], int L, int D, int H)
    {
        if (H)
        {
            int buffer[cols];
            for (int i = 1; i <= cols; ++i)
                buffer[i - 1] = A[L][i];
            for (int i = 0; i < cols; ++i)
                A[L][1 + (i + D) % cols] = buffer[i];
        }
        else
        {
            int buffer[rows];
            for (int i = 1; i <= rows; ++i)
                buffer[i - 1] = A[i][L];
            for (int i = 0; i < rows; ++i)
                A[1 + (i + D) % rows][L] = buffer[i];
        }
    }

    inline void evaluate_update(int & sc, int & sr, int & ec, int & er, int I, int J, int K)
    {
        if (K)
        {
            sc = 1;  sr = I;  ec = 1 + J;  er = I;
        }
        else
        {
            sc = I;  sr = 1;  ec = I;  er = 1 + J;
        }
    }

    void search_move(int & sc, int & sr, int & ec, int & er, int A[height][width])
    {
        int I, J, K, T, V = -1;
        for (int i = 1, boundI = i + rows; i < boundI; ++i)
        {
            for (int j = 1; j < cols; ++j)
            {
                shift_board(A, i, j, 1);
                T = evaluate_board(A);
                shift_board(A, i, cols - j, 1);
                if (V < T)
                {
                    V = T;  I = i;  J = j;  K = 1;
                }
            }
        }
        for (int i = 1, boundI = i + cols; i < boundI; ++i)
        {
            for (int j = 1; j < rows; ++j)
            {
                shift_board(A, i, j, 0);
                T = evaluate_board(A);
                shift_board(A, i, rows - j, 0);
                if (V < T)
                {
                    V = T;  I = i;  J = j;  K = 0;
                }
            }
        }
        //printf("V: %d\n", V);
        evaluate_update(sc, sr, ec, er, I, J, K);
    }

    PotionCoord find_optimal_move(int A[rows][cols])
    {
        int __A[height][width] = {  0  };
        for (int i = 1, boundI = i + rows; i < boundI; ++i)
        {
            for (int j = 1, boundJ = j + cols; j < boundJ; ++j)
            {
                __A[i][j] = A[i - 1][j - 1];
            }
        }
        int sc, sr, ec, er;
        search_move(sc, sr, ec, er, __A);
        return PotionCoord(sc - 1, sr - 1, ec - 1, er - 1);
    }

    void shift_board_basic(int A[rows][cols], int L, int D, int H)
    {
        if (H)
        {
            int buffer[cols];
            for (int i = 0; i < cols; ++i)
                buffer[i] = A[L][i];
            for (int i = 0; i < cols; ++i)
                A[L][(i + D) % cols] = buffer[i];
        }
        else
        {
            int buffer[rows];
            for (int i = 0; i < rows; ++i)
                buffer[i] = A[i][L];
            for (int i = 0; i < rows; ++i)
                A[(i + D) % rows][L] = buffer[i];
        }
    }

    void print_board(int A[rows][cols])
    {
        for (int i = 0; i < rows; ++i)
        {
            for (int j = 0; j < cols; ++j)
            {
                printf("%d ", A[i][j]);
            }
            printf("\n");
        }
        printf("\n");
    }

    inline void SE2IJK(int & I, int & J, int & K, int sc, int sr, int ec, int er)
    {
        if (sc == ec)
        {
            K = 0;  I = sc;  J = er - sr;
        }
        else
        {
            K = 1;  I = sr;  J = ec - sc;
        }
    }
}

#endif // H_POTION_UTILS
