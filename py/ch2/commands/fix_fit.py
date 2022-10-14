
from logging import getLogger
from sys import stdout, stderr

from .args import PATH, DROP, OUTPUT, SLICES, RAW, WARN, MIN_SYNC_CNT, MAX_RECORD_LEN, MAX_DROP_CNT, MAX_BACK_CNT, \
    MAX_FWD_LEN, DISCARD, FORCE, VALIDATE, ADD_HEADER, HEADER_SIZE, PROTOCOL_VERSION, PROFILE_VERSION, MAX_DELTA_T, \
    NAME, FIX_HEADER, FIX_CHECKSUM, NAME_BAD, NAME_GOOD, START
from ..common.args import mm, no
from ..fit.fix import fix
from ..fit.profile.profile import read_fit

log = getLogger(__name__)


def fix_fit(config):
    '''
## fix-fit

    > ch2 fix-fit PATH -o PATH --drop

Try to fix a corrupted fit file.

If `--header` is specified then a new header is prepended at the start of the data.

If `--slices` is specified then the given slices are taken from the data and used to construct a new file.

If `--drop` is specified then the program tries to find appropriate slices by discarding data until all the
remaining data can be parsed.

If `--fix-header` is specified then the header is corercted.

If `--fix-checksum` is specified then the checksum is corrected.

### Examples

    > ch2 fix-fit FILE.FIT --slices 1000: --fix-header --fix-checksum

Will attempt to drop the first 1000 bytes from the given file.

    > ch2 fix-fit data/tests/personal/8CS90646.FIT --drop --fix-header --fix-checksum

Will attempt to fix the given file (in the test data from git).

    > ch2 fix-fit FILE.FIT --add-header --header-size 14 --slices :14,28: --fix-header --fix-checksum

Will prepend a new 14 byte header, drop the old 14 byte header, and fix the header and checksum values.
    '''

    args = config.args
    check = args[NAME] is not None
    if check:
        name = NAME_GOOD if args[NAME] else NAME_BAD
        if args[ADD_HEADER] or args[DROP] or args[SLICES] or args[START] or args[FIX_HEADER] or args[FIX_CHECKSUM]:
            raise Exception(f'Cannot check ({mm(name)}) and modify at the same time')
        if not args[VALIDATE]:
            raise Exception(f'{mm(name)} and {no(VALIDATE)} makes no sense, numpty')
    if not args[FORCE]:
        log.warning(f'{no(FORCE)} means that data are not completely parsed')

    for path in args[PATH]:

        log.info('Input ----------')
        log.info(f'Reading binary data from {path}')
        data = read_fit(path)
        log.debug('Read %d bytes' % len(data))

        try:
            data = fix(data, warn=args[WARN],
                       add_header=args[ADD_HEADER], drop=args[DROP], slices=args[SLICES], start=args[START],
                       fix_header=args[FIX_HEADER], fix_checksum=args[FIX_CHECKSUM],
                       force=args[FORCE], validate=args[VALIDATE],
                       header_size=args[HEADER_SIZE], protocol_version=args[PROTOCOL_VERSION],
                       profile_version=args[PROFILE_VERSION], min_sync_cnt=args[MIN_SYNC_CNT],
                       max_record_len=args[MAX_RECORD_LEN], max_drop_cnt=args[MAX_DROP_CNT],
                       max_back_cnt=args[MAX_BACK_CNT], max_fwd_len=args[MAX_FWD_LEN], max_delta_t=args[MAX_DELTA_T])
        except:
            if not check:
                raise
            if not args[NAME]:
                print(path)
        else:
            if check and args[NAME]:
                print(path)

        if check:
            # interleave logging and names
            stderr.flush()
            stdout.flush()
        else:
            log.info('Output ----------')
            if args[DISCARD]:
                log.info('Discarded output')
            else:
                if out_path := args[OUTPUT]:
                    log.info(f'Writing binary data to {out_path}')
                    with open(out_path, 'wb') as out:
                        out.write(data)
                elif args[RAW]:
                    log.info('Writing binary data to stdout')
                    stdout.buffer.write(data)
                else:
                    log.info('Writing hex data to stdout')
                    stdout.write(data.hex())
                log.debug('Wrote %d bytes' % len(data))

