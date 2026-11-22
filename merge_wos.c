/*
 * merge_wos.c - Junta varios arquivos exportados da Web of Science
 *               (formato "Plain text file" / "Full Record and Cited References")
 *               em um unico arquivo .txt compativel com o VOSviewer.
 *
 * Formato WoS: cada arquivo comeca com
 *     FN Clarivate Analytics Web of Science
 *     VR 1.0
 * seguido de registros (cada um termina com a linha "ER") e termina com "EF".
 *
 * O programa:
 *   - escreve o cabecalho FN/VR uma unica vez;
 *   - copia todos os registros de todos os arquivos;
 *   - remove duplicatas pelo campo UT (ex.: "UT WOS:000123456700001");
 *   - remove BOM UTF-8 e converte CRLF -> LF;
 *   - escreve "EF" uma unica vez no final.
 *
 * Compilar:  gcc -O2 -Wall -o merge_wos merge_wos.c
 * Usar:      ./merge_wos <pasta_com_txt> <saida.txt>
 *            ./merge_wos <saida.txt> arq1.txt arq2.txt ...   (modo lista)
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <dirent.h>
#include <sys/stat.h>

#define LINE_MAX_LEN 65536
#define HASH_SIZE 262144 /* potencia de 2, folgado para dezenas de milhares */

/* ---------- conjunto de UTs (tabela hash com encadeamento) ---------- */
typedef struct Node { char *key; struct Node *next; } Node;
static Node *table[HASH_SIZE];

static unsigned long hash_str(const char *s) {
    unsigned long h = 5381;
    while (*s) h = ((h << 5) + h) + (unsigned char)*s++;
    return h & (HASH_SIZE - 1);
}

/* retorna 1 se inseriu (novo), 0 se ja existia */
static int set_add(const char *key) {
    unsigned long h = hash_str(key);
    for (Node *n = table[h]; n; n = n->next)
        if (strcmp(n->key, key) == 0) return 0;
    Node *n = malloc(sizeof *n);
    n->key = strdup(key);
    n->next = table[h];
    table[h] = n;
    return 1;
}

/* ---------- buffer dinamico para um registro ---------- */
typedef struct { char *data; size_t len, cap; } Buf;

static void buf_append(Buf *b, const char *s) {
    size_t l = strlen(s);
    if (b->len + l + 1 > b->cap) {
        b->cap = (b->len + l + 1) * 2;
        b->data = realloc(b->data, b->cap);
    }
    memcpy(b->data + b->len, s, l + 1);
    b->len += l;
}

static void chomp(char *s) {
    size_t l = strlen(s);
    while (l && (s[l - 1] == '\n' || s[l - 1] == '\r')) s[--l] = '\0';
}

static long total_lidos = 0, total_escritos = 0, total_dup = 0, total_sem_ut = 0;

static void processa_arquivo(const char *path, FILE *out) {
    FILE *in = fopen(path, "r");
    if (!in) { fprintf(stderr, "Aviso: nao abriu %s\n", path); return; }

    static char line[LINE_MAX_LEN];
    Buf rec = {0};
    char ut[256] = "";
    int em_registro = 0, primeira = 1;
    long lidos = 0, escritos = 0;

    while (fgets(line, sizeof line, in)) {
        char *p = line;
        if (primeira) { /* remove BOM UTF-8 */
            if ((unsigned char)p[0] == 0xEF && (unsigned char)p[1] == 0xBB &&
                (unsigned char)p[2] == 0xBF) p += 3;
            primeira = 0;
        }
        chomp(p);

        /* cabecalho / rodape de cada arquivo: ignorados */
        if (!em_registro && (strncmp(p, "FN ", 3) == 0 || strncmp(p, "VR ", 3) == 0 ||
                             strcmp(p, "EF") == 0 || p[0] == '\0'))
            continue;

        if (!em_registro) { em_registro = 1; rec.len = 0; if (rec.data) rec.data[0] = '\0'; ut[0] = '\0'; }

        if (strncmp(p, "UT ", 3) == 0) {
            strncpy(ut, p + 3, sizeof ut - 1);
            ut[sizeof ut - 1] = '\0';
        }
        buf_append(&rec, p);
        buf_append(&rec, "\n");

        if (strcmp(p, "ER") == 0) { /* fim do registro */
            lidos++;
            int novo = 1;
            if (ut[0]) novo = set_add(ut); else total_sem_ut++;
            if (novo) { fputs(rec.data, out); fputs("\n", out); escritos++; }
            else total_dup++;
            em_registro = 0;
        }
    }
    if (em_registro) fprintf(stderr, "Aviso: %s terminou no meio de um registro (ignorado)\n", path);

    fclose(in);
    free(rec.data);
    total_lidos += lidos; total_escritos += escritos;
    printf("  %-50s registros: %6ld  novos: %6ld\n", path, lidos, escritos);
}

static int cmp_str(const void *a, const void *b) {
    return strcmp(*(char * const *)a, *(char * const *)b);
}

static int termina_com_txt(const char *n) {
    size_t l = strlen(n);
    return l > 4 && strcmp(n + l - 4, ".txt") == 0;
}

int main(int argc, char **argv) {
    if (argc < 3) {
        fprintf(stderr, "Uso: %s <pasta_com_txt> <saida.txt>\n"
                        "     %s <saida.txt> arq1.txt arq2.txt ...\n", argv[0], argv[0]);
        return 1;
    }

    char **arquivos = NULL; int n = 0;
    const char *saida;
    struct stat st;

    if (argc == 3 && stat(argv[1], &st) == 0 && S_ISDIR(st.st_mode)) {
        saida = argv[2];
        DIR *d = opendir(argv[1]);
        if (!d) { perror(argv[1]); return 1; }
        struct dirent *e;
        while ((e = readdir(d))) {
            if (!termina_com_txt(e->d_name)) continue;
            char *full = malloc(strlen(argv[1]) + strlen(e->d_name) + 2);
            sprintf(full, "%s/%s", argv[1], e->d_name);
            arquivos = realloc(arquivos, sizeof(char *) * (n + 1));
            arquivos[n++] = full;
        }
        closedir(d);
        qsort(arquivos, n, sizeof(char *), cmp_str);
    } else {
        saida = argv[1];
        n = argc - 2;
        arquivos = argv + 2;
    }

    FILE *out = fopen(saida, "w");
    if (!out) { perror(saida); return 1; }

    fputs("FN Clarivate Analytics Web of Science\nVR 1.0\n", out);
    printf("Juntando %d arquivo(s):\n", n);
    for (int i = 0; i < n; i++) {
        if (strcmp(arquivos[i], saida) == 0) continue; /* nao ler a propria saida */
        processa_arquivo(arquivos[i], out);
    }
    fputs("EF\n", out);
    fclose(out);

    printf("\nTotal lidos: %ld | gravados: %ld | duplicados removidos: %ld | sem UT: %ld\n",
           total_lidos, total_escritos, total_dup, total_sem_ut);
    printf("Arquivo final: %s\n", saida);
    return 0;
}
