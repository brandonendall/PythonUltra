// PythonUltra PicoC platform adapter for the Casio fx-CG50.
// PicoC upstream is BSD-3-Clause; see vendor/picoc/LICENSE after bootstrap.

#include "vendor/picoc/picoc.h"
#include "vendor/picoc/interpreter.h"
#include "py/mphal.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/stat.h>

void PlatformInit(Picoc *pc)
{
    (void)pc;
}

void PlatformCleanup(Picoc *pc)
{
    (void)pc;
}

/* PythonUltra supplies editor/terminal input itself. Interactive PicoC will be
   connected to that input path in the next integration stage. */
char *PlatformGetLine(char *buf, int max_len, const char *prompt)
{
    (void)buf;
    (void)max_len;
    if(prompt != NULL)
        mp_hal_stdout_tx_strn(prompt, strlen(prompt));
    return NULL;
}

int PlatformGetCharacter(void)
{
    return -1;
}

void PlatformPutc(unsigned char out_ch, union OutputStreamInfo *stream)
{
    (void)stream;
    char ch = (char)out_ch;
    mp_hal_stdout_tx_strn(&ch, 1);
}

char *PlatformReadFile(Picoc *pc, const char *filename)
{
    struct stat info;
    if(stat(filename, &info) != 0)
        ProgramFailNoParser(pc, "can't read file %s", filename);

    FILE *fp = fopen(filename, "rb");
    if(fp == NULL)
        ProgramFailNoParser(pc, "can't read file %s", filename);

    char *text = malloc((size_t)info.st_size + 1);
    if(text == NULL) {
        fclose(fp);
        ProgramFailNoParser(pc, "out of memory");
    }

    size_t count = fread(text, 1, (size_t)info.st_size, fp);
    fclose(fp);
    text[count] = '\0';
    return text;
}

void PicocPlatformScanFile(Picoc *pc, const char *filename)
{
    char *source = PlatformReadFile(pc, filename);
    if(source != NULL && source[0] == '#' && source[1] == '!') {
        source[0] = '/';
        source[1] = '/';
    }
    PicocParse(pc, filename, source, (int)strlen(source), true, false, true,
        false);
}

void PlatformExit(Picoc *pc, int ret_val)
{
    pc->PicocExitValue = ret_val;
    longjmp(pc->PicocExitBuf, 1);
}

/* Calculator-specific native C functions will be registered here later. */
void PlatformLibraryInit(Picoc *pc)
{
    (void)pc;
}
