# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from cffi import FFI

##########
# Header definitions
##########

_groove_header = r"""
int groove_init(void);
void groove_finish(void);
void groove_set_logging(int level);

int groove_channel_layout_count(uint64_t channel_layout);
uint64_t groove_channel_layout_default(int count);

enum GrooveSampleFormat {
    GROOVE_SAMPLE_FMT_NONE = -1,
    GROOVE_SAMPLE_FMT_U8,
    GROOVE_SAMPLE_FMT_S16,
    GROOVE_SAMPLE_FMT_S32,
    GROOVE_SAMPLE_FMT_FLT,
    GROOVE_SAMPLE_FMT_DBL,

    GROOVE_SAMPLE_FMT_U8P,
    GROOVE_SAMPLE_FMT_S16P,
    GROOVE_SAMPLE_FMT_S32P,
    GROOVE_SAMPLE_FMT_FLTP,
    GROOVE_SAMPLE_FMT_DBLP,
};

struct GrooveAudioFormat {
    int sample_rate;
    uint64_t channel_layout;
    enum GrooveSampleFormat sample_fmt;
};

int groove_sample_format_bytes_per_sample(enum GrooveSampleFormat format);

int groove_audio_formats_equal(const struct GrooveAudioFormat *a, const struct GrooveAudioFormat *b);

int groove_version_major(void);
int groove_version_minor(void);
int groove_version_patch(void);
const char *groove_version(void);

struct GrooveFile {
    int dirty;
    const char *filename;
};

struct GrooveTag;

const char *groove_tag_key(struct GrooveTag *tag);
const char *groove_tag_value(struct GrooveTag *tag);

struct GrooveFile *groove_file_open(const char *filename);
void groove_file_close(struct GrooveFile *file);

struct GrooveTag *groove_file_metadata_get(struct GrooveFile *file,
        const char *key, const struct GrooveTag*prev, int flags);

int groove_file_metadata_set(struct GrooveFile *file, const char *key,
        const char *value, int flags);

const char *groove_file_short_names(struct GrooveFile *file);

int groove_file_save(struct GrooveFile *file);

double groove_file_duration(struct GrooveFile *file);

void groove_file_audio_format(struct GrooveFile *file,
        struct GrooveAudioFormat *audio_format);

struct GroovePlaylistItem {
    struct GrooveFile *file;
    double gain;
    double peak;
    struct GroovePlaylistItem *prev;
    struct GroovePlaylistItem *next;
};

struct GroovePlaylist {
    struct GroovePlaylistItem *head;
    struct GroovePlaylistItem *tail;
    double gain;
};

struct GroovePlaylist *groove_playlist_create(void);

void groove_playlist_destroy(struct GroovePlaylist *playlist);

void groove_playlist_play(struct GroovePlaylist *playlist);
void groove_playlist_pause(struct GroovePlaylist *playlist);

void groove_playlist_seek(struct GroovePlaylist *playlist,
        struct GroovePlaylistItem *item, double seconds);

struct GroovePlaylistItem *groove_playlist_insert(
        struct GroovePlaylist *playlist, struct GrooveFile *file,
        double gain, double peak,
        struct GroovePlaylistItem *next);

void groove_playlist_remove(struct GroovePlaylist *playlist,
        struct GroovePlaylistItem *item);

void groove_playlist_position(struct GroovePlaylist *playlist,
        struct GroovePlaylistItem **item, double *seconds);

int groove_playlist_playing(struct GroovePlaylist *playlist);

void groove_playlist_clear(struct GroovePlaylist *playlist);

int groove_playlist_count(struct GroovePlaylist *playlist);

void groove_playlist_set_gain(struct GroovePlaylist *playlist, double gain);

void groove_playlist_set_item_gain(struct GroovePlaylist *playlist,
        struct GroovePlaylistItem *item, double gain);

void groove_playlist_set_item_peak(struct GroovePlaylist *playlist,
        struct GroovePlaylistItem *item, double peak);

void groove_playlist_set_fill_mode(struct GroovePlaylist *playlist, int mode);

struct GrooveBuffer {
    uint8_t **data;
    struct GrooveAudioFormat format;
    int frame_count;
    struct GroovePlaylistItem *item;
    double pos;
    int size;
    uint64_t pts;
};

void groove_buffer_ref(struct GrooveBuffer *buffer);
void groove_buffer_unref(struct GrooveBuffer *buffer);

struct GrooveSink {
    struct GrooveAudioFormat audio_format;
    int disable_resample;
    int buffer_sample_count;
    int buffer_size;
    double gain;
    void *userdata;
    void (*flush)(struct GrooveSink *);
    void (*purge)(struct GrooveSink *, struct GroovePlaylistItem *);
    void (*play)(struct GrooveSink *);

    struct GroovePlaylist *playlist;

    int bytes_per_sec;
};

struct GrooveSink *groove_sink_create(void);
void groove_sink_destroy(struct GrooveSink *sink);

int groove_sink_attach(struct GrooveSink *sink, struct GroovePlaylist *playlist);
int groove_sink_detach(struct GrooveSink *sink);

int groove_sink_buffer_get(struct GrooveSink *sink,
        struct GrooveBuffer **buffer, int block);

int groove_sink_buffer_peek(struct GrooveSink *sink, int block);

int groove_sink_set_gain(struct GrooveSink *sink, double gain);
"""

_queue_header = r"""
struct GrooveQueue {
    void *context;
    void (*cleanup)(struct GrooveQueue*, void *obj);
    void (*put)(struct GrooveQueue*, void *obj);
    void (*get)(struct GrooveQueue*, void *obj);
    void (*purge)(struct GrooveQueue*, void *obj);
};

struct GrooveQueue *groove_queue_create(void);

void groove_queue_flush(struct GrooveQueue *queue);

void groove_queue_destroy(struct GrooveQueue *queue);

void groove_queue_abort(struct GrooveQueue *queue);
void groove_queue_reset(struct GrooveQueue *queue);

int groove_queue_put(struct GrooveQueue *queue, void *obj);

int groove_queue_get(struct GrooveQueue *queue, void **obj_ptr, int block);

int groove_queue_peek(struct GrooveQueue *queue, int block);

void groove_queue_purge(struct GrooveQueue *queue);

void groove_queue_cleanup_default(struct GrooveQueue *queue, void *obj);
"""

_encoder_header = r"""
struct GrooveEncoder {
    struct GrooveAudioFormat target_audio_format;
    int bit_rate;
    const char *format_short_name;
    const char *codec_short_name;
    const char *filename;
    const char *mime_type;
    int sink_buffer_size;
    int encoded_buffer_size;
    double gain;
    struct GroovePlaylist *playlist;
    struct GrooveAudioFormat actual_audio_format;
};

struct GrooveEncoder *groove_encoder_create(void);
void groove_encoder_destroy(struct GrooveEncoder *encoder);

int groove_encoder_attach(struct GrooveEncoder *encoder,
        struct GroovePlaylist *playlist);
int groove_encoder_detach(struct GrooveEncoder *encoder);

int groove_encoder_buffer_get(struct GrooveEncoder *encoder,
        struct GrooveBuffer **buffer, int block);

int groove_encoder_buffer_peek(struct GrooveEncoder *encoder, int block);

struct GrooveTag *groove_encoder_metadata_get(struct GrooveEncoder *encoder,
        const char *key, const struct GrooveTag *prev, int flags);

int groove_encoder_metadata_set(struct GrooveEncoder *encoder, const char *key,
        const char *value, int flags);

void groove_encoder_position(struct GrooveEncoder *encoder,
        struct GroovePlaylistItem **item, double *seconds);

int groove_encoder_set_gain(struct GrooveEncoder *encoder, double gain);
"""

##########
# FFI Build
##########

_groove_source = r"""
#include <groove/groove.h>
#include <groove/queue.h>
#include <groove/encoder.h>
"""
ffi_groove = FFI()
ffi_groove.set_source('groove._groove', _groove_source, libraries=['groove'])
ffi_groove.cdef(_groove_header)
ffi_groove.cdef(_queue_header)
ffi_groove.cdef(_encoder_header)

if __name__ == '__main__':
    ffi_groove.compile()
