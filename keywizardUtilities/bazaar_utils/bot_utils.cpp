#include <algorithm>
#include <cstring>

#define OPTIMIZE_GET_BOUNDARY 0

class BOUND
{
public:
    size_t SX, EX;
    BOUND(size_t SX = 0, size_t EX = 0) : SX(SX), EX(EX) {  ;  }
};

namespace BotUtils
{
    typedef unsigned char UINT8;
    BOUND get_boundary(UINT8 image[], size_t height, size_t width)
    {
        BOUND boundary(0, 0);
        #if (OPTIMIZE_GET_BOUNDARY == 0)
        size_t i, j, k;
        for (j = 0, k = 0; j < width; ++j)
        {
            for (i = 0; i < height; ++i)
            {
                if (image[i * width + j])
                {
                    boundary.SX = j;
                    k = 1;
                    break;
                }
            }
            if (k)
            {
                break;
            }
        }
        for (j = width - 1, k = 0; j < width; --j)
        {
            for (i = 0; i < height; ++i)
            {
                if (image[i * width + j])
                {
                    boundary.EX = j;
                    k = 1;
                    break;
                }
            }
            if (k)
            {
                break;
            }
        }
        #endif
        #if (OPTIMIZE_GET_BOUNDARY == 1)
        size_t i = height / 2, j;
        for (j = 0; j < width; ++j)
        {
            if (image[i * width + j])
            {
                boundary.SX = j;
                break;
            }
        }
        for (j = width - 1; j < width; --j)
        {
            if (image[i * width + j])
            {
                boundary.EX = j;
                break;
            }
        }
        #endif
        return boundary;
    }
    size_t get_multiple_boundary(size_t SX[], size_t EX[], UINT8 imageList[], size_t images, size_t height, size_t width)
    {
        BOUND boundary;
        for (size_t k = 0; k < images; ++k)
        {
            boundary = get_boundary(&(imageList[ k * height * width ]), height, width);
            SX[k] = boundary.SX;
            EX[k] = boundary.EX;
            if (boundary.SX == boundary.EX)
            {
                return k;
            }
        }
        return images;
    }

    constexpr size_t MAX_LCS_LEN = 100;

    size_t LCS_TABLE[MAX_LCS_LEN + 1][MAX_LCS_LEN + 1] = {  0  };

    size_t LCS(char sequenceA[], char sequenceB[], size_t lenA, size_t lenB)
    {
        size_t i, j;
        for (i = 1; i <= lenA; ++i)
        {
            for (j = 1; j <= lenB; ++j)
            {
                if (sequenceA[i - 1] == sequenceB[j - 1])
                {
                    LCS_TABLE[i][j] = LCS_TABLE[i - 1][j - 1] + 1;
                }
                else if (LCS_TABLE[i - 1][j] < LCS_TABLE[i][j - 1])
                {
                    LCS_TABLE[i][j] = LCS_TABLE[i][j - 1];
                }
                else
                {
                    LCS_TABLE[i][j] = LCS_TABLE[i - 1][j];
                }
            }
        }
        return LCS_TABLE[lenA][lenB];
    }
    size_t select_items_by_name(size_t __namesWanted[], size_t __namesFound[], char ** namesWanted, char ** namesFound, size_t numWanted, size_t numFound, double nameThresh)
    {
        size_t i, j, k = 0, lenA, lenB;  char * nameWanted, * nameFound;  double score;
        for (i = 0; i < numWanted; ++i)
        {
            for (j = 0; j < numFound; ++j)
            {
                nameWanted = namesWanted[i];
                nameFound  = namesFound[j];
                lenA       = strlen(nameWanted);
                lenB       = strlen(nameFound);
                if ((lenA == lenB) && (strcmp(nameWanted, nameFound) == 0))
                {
                    __namesWanted[k] = i;
                    __namesFound[k]  = j;
                    k++;
                }
                else
                {
                    score = (double) LCS(nameWanted, nameFound, lenA, lenB) / std::max(lenA, lenB);
                    if (score >= nameThresh)
                    {
                        __namesWanted[k] = i;
                        __namesFound[k]  = j;
                        k++;
                    }
                }
            }
        }
        return k;
    }

    constexpr size_t MAX_COLORS = 256;

    void get_bounding_box(size_t * sx, size_t * sy, size_t * ex, size_t * ey, UINT8 image[], size_t height, size_t width, UINT8 color)
    {
        size_t minI = height - 1, minJ = width - 1, maxI = 0, maxJ = 0, i, j;
        for (i = 0; i < height; ++i)
        {
            for (j = 0; j < width; ++j)
            {
                if (image[i * width + j] == color)
                {
                    if (i < minI)
                        minI = i;
                    if (j < minJ)
                        minJ = j;
                    if (i > maxI)
                        maxI = i;
                    if (j > maxJ)
                        maxJ = j;
                }
            }
        }
        *sx = minJ;
        *sy = minI;
        *ex = maxJ + 1;
        *ey = maxI + 1;
    }
    size_t get_bounding_boxes(size_t sx[], size_t sy[], size_t ex[], size_t ey[], UINT8 image[], size_t height, size_t width)
    {
        UINT8 colors[MAX_COLORS], present[MAX_COLORS] = {  0  }, color;  size_t counter = 0, i, j;
        for (j = 0; j < width; ++j)
        {
            for (i = 0; i < height; ++i)
            {
                color = image[i * width + j];
                if ((color != 0) && (present[color] == 0))
                {
                    colors[counter++] = color;
                    present[color] = 1;
                }
            }
        }
        for (i = 0; i < counter; ++i)
        {
            get_bounding_box(&(sx[i]), &(sy[i]), &(ex[i]), &(ey[i]), image, height, width, colors[i]);
        }
        return counter;
    }
    size_t select_items_by_quantity(size_t __indicesFound[], size_t quantityWanted[], size_t quantityFound[], size_t indicesFound[], size_t numItems)
    {
        size_t i, j, k = 0;
        for (i = 0; i < numItems; ++i)
        {
            if (quantityWanted[i] <= quantityFound[i])
            {
                __indicesFound[k++] = indicesFound[i];
            }
        }
        return k;
    }
}

extern "C"
{
    typedef unsigned char UINT8;
    namespace BU = BotUtils;
    size_t get_multiple_boundary(size_t SX[], size_t EX[], UINT8 imageList[], size_t images, size_t height, size_t width)
    {
        return BU::get_multiple_boundary(SX, EX, imageList, images, height, width);
    }
    size_t select_items_by_name(size_t __namesWanted[], size_t __namesFound[], char ** namesWanted, char ** namesFound, size_t numWanted, size_t numFound, double nameThresh)
    {
        return BU::select_items_by_name(__namesWanted, __namesFound, namesWanted, namesFound, numWanted, numFound, nameThresh);
    }
    size_t get_bounding_boxes(size_t sx[], size_t sy[], size_t ex[], size_t ey[], UINT8 image[], size_t height, size_t width)
    {
        return BU::get_bounding_boxes(sx, sy, ex, ey, image, height, width);
    }
    size_t select_items_by_quantity(size_t __indicesFound[], size_t quantityWanted[], size_t quantityFound[], size_t indicesFound[], size_t numItems)
    {
        return BU::select_items_by_quantity(__indicesFound, quantityWanted, quantityFound, indicesFound, numItems);
    }
}

int main()
{


    return 0;
}
