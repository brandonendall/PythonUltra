#include <stdio.h>
#include <stdlib.h>
#include <string.h>

/*
 PythonUltra PicoC hardware smoke test
 Exercises:
 - parsing
 - main()
 - arithmetic
 - if/else
 - loops
 - functions
 - arrays
 - pointers
 - strings
 - malloc/free
 - printf / terminal output
*/

static int add(int a, int b)
{
    return a + b;
}

int main(void)
{
    int failures = 0;

    printf("PythonUltra PicoC Test\n");
    printf("=====================\n");

    {
        int result = add(7, 5);
        printf("T1 arithmetic: 7 + 5 = %d\n", result);
        if(result == 12)
            printf("T1 PASS\n");
        else {
            printf("T1 FAIL\n");
            failures++;
        }
    }

    {
        int i;
        int sum = 0;
        for(i = 1; i <= 5; i++)
            sum += i;

        printf("T2 loop sum 1..5 = %d\n", sum);
        if(sum == 15)
            printf("T2 PASS\n");
        else {
            printf("T2 FAIL\n");
            failures++;
        }
    }

    {
        int values[4] = {3, 6, 9, 12};
        int total = values[0] + values[1] + values[2] + values[3];

        printf("T3 array total = %d\n", total);
        if(total == 30)
            printf("T3 PASS\n");
        else {
            printf("T3 FAIL\n");
            failures++;
        }
    }

    {
        int value = 42;
        int *ptr = &value;

        printf("T4 pointer value = %d\n", *ptr);
        if(*ptr == 42)
            printf("T4 PASS\n");
        else {
            printf("T4 FAIL\n");
            failures++;
        }
    }

    {
        char text[32];
        strcpy(text, "PicoC");
        strcat(text, " works");

        printf("T5 string = %s\n", text);
        if(strcmp(text, "PicoC works") == 0)
            printf("T5 PASS\n");
        else {
            printf("T5 FAIL\n");
            failures++;
        }
    }

    {
        int *numbers = (int *)malloc(3 * sizeof(int));

        if(numbers == NULL) {
            printf("T6 malloc FAIL\n");
            failures++;
        }
        else {
            numbers[0] = 10;
            numbers[1] = 20;
            numbers[2] = 30;

            printf("T6 malloc total = %d\n",
                numbers[0] + numbers[1] + numbers[2]);

            if(numbers[0] + numbers[1] + numbers[2] == 60)
                printf("T6 PASS\n");
            else {
                printf("T6 FAIL\n");
                failures++;
            }

            free(numbers);
        }
    }

    printf("=====================\n");

    if(failures == 0) {
        printf("ALL C TESTS PASSED\n");
        return 0;
    }

    printf("C TEST FAILURES: %d\n", failures);
    return failures;
}
