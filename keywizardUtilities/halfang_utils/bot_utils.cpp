#include <cstdlib>
#include <cstdio>
#include <ctime>

namespace BotUtils
{

    static const int QUANTITY_MAX = 7;

    static const int CARD_ATTACK  = 0,
                     CARD_ENCHANT = 1,
                     CARD_HEAL    = 2,
                     CARD_GREY    = 3;

    static const int ACTION_ATTACK  = 0,
                     ACTION_ENCHANT = 1,
                     ACTION_HEAL    = 2,
                     ACTION_PASS    = 3;

    inline int random_randint(int start, int end)
    {
        int interval = end - start;
        return start + (rand() % interval);
    }

    inline void set_random_seed()
    {
        srand(time(NULL));
    }

    int determine_moves(int * firstCard, int * secondCard, int cardList[], int numCards, int shouldHeal)
    {
        int attackCards[QUANTITY_MAX], enchantCards[QUANTITY_MAX], healCards[QUANTITY_MAX];
        int a = 0, e = 0, h = 0, i;
        for (i = 0; i < numCards; ++i)
        {
            if (cardList[i] == CARD_ATTACK)
                attackCards[a++] = i;
            else if (cardList[i] == CARD_ENCHANT)
                enchantCards[e++] = i;
            else if (cardList[i] == CARD_HEAL)
                healCards[h++] = i;
        }
        if ((shouldHeal) && (h))
        {
            *firstCard = healCards[0];
            return ACTION_HEAL;
        }
        else if ((e) && (a))
        {
            *firstCard  = enchantCards[random_randint(0, e)];
            *secondCard = attackCards[random_randint(0, a)];
            return ACTION_ENCHANT;
        }
        else if (a)
        {
            *firstCard = attackCards[random_randint(0, a)];
            return ACTION_ATTACK;
        }
        else
        {
            return ACTION_PASS;
        }
    }
}
extern "C"
{
    void initialize_library()
    {
        BotUtils::set_random_seed();
    }
    int determine_moves(int * firstCard, int * secondCard, int cardList[], int numCards, int shouldHeal)
    {
        return BotUtils::determine_moves(firstCard, secondCard, cardList, numCards, shouldHeal);
    }
}
int main()
{
    int cardList[] = {  0, 1, 0, 2, 3, 3, 1  }, numCards = sizeof(cardList) / sizeof(int);
    int firstCard = -1, secondCard = -1, shouldHeal = 0;
    BotUtils::set_random_seed();
    int actionType = BotUtils::determine_moves(&firstCard, &secondCard, cardList, numCards, shouldHeal);
    printf("Type: %d;  First: %d;  Second: %d\n", actionType, firstCard, secondCard);

    return 0;
}
