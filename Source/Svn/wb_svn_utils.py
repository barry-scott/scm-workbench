'''
 ====================================================================
 Copyright (c) 2003-2016 Barry A Scott.  All rights reserved.

 This software is licensed as described in the file LICENSE.txt,
 which you should have received as part of this distribution.

 ====================================================================

    wb_svn_utils.py

'''
import pysvn

# code assumes svn 1.9 as a minimum version
class SvnVersionInfo:
    #
    # Keep infos about the features of the available pysvn version
    #
    def __init__(self):
        pass
        # add svn features tests here

version_info = SvnVersionInfo()

wc_status_kind_map = {
pysvn.wc_status_kind.missing:       '?',
pysvn.wc_status_kind.added:         'A',
pysvn.wc_status_kind.conflicted:    'C',
pysvn.wc_status_kind.deleted:       'D',
pysvn.wc_status_kind.external:      'X',
pysvn.wc_status_kind.ignored:       'I',
pysvn.wc_status_kind.incomplete:    '!',
pysvn.wc_status_kind.missing:       '!',
pysvn.wc_status_kind.merged:        'G',
pysvn.wc_status_kind.modified:      'M',
pysvn.wc_status_kind.none:          ' ',
pysvn.wc_status_kind.normal:        ' ',
pysvn.wc_status_kind.obstructed:    '~',
pysvn.wc_status_kind.replaced:      'R',
pysvn.wc_status_kind.unversioned:   ' ',
}

# lookup the status and see if it means the file will be checked in
wc_status_checkin_map = {
pysvn.wc_status_kind.missing:       False,
pysvn.wc_status_kind.added:         True,
pysvn.wc_status_kind.conflicted:    True,       # allow user to see the conflicted file
pysvn.wc_status_kind.deleted:       True,
pysvn.wc_status_kind.external:      False,
pysvn.wc_status_kind.ignored:       False,
pysvn.wc_status_kind.incomplete:    False,
pysvn.wc_status_kind.missing:       False,
pysvn.wc_status_kind.merged:        True,
pysvn.wc_status_kind.modified:      True,
pysvn.wc_status_kind.none:          False,
pysvn.wc_status_kind.normal:        False,
pysvn.wc_status_kind.obstructed:    False,
pysvn.wc_status_kind.replaced:      True,
pysvn.wc_status_kind.unversioned:   False,
}

# return a value used to sort by status
#  1-10 - text status
# 11-20 - prop status
# 21-30 - other status

wc_status_kind_text_sort_map = {
# need use to update
pysvn.wc_status_kind.missing:       1,
pysvn.wc_status_kind.incomplete:    1,
pysvn.wc_status_kind.obstructed:    1,

# user needs to sort this one out
pysvn.wc_status_kind.conflicted:    2,

# need user to checkin
pysvn.wc_status_kind.deleted:       3,
pysvn.wc_status_kind.added:         4,
pysvn.wc_status_kind.modified:      4,

# other controlled files
pysvn.wc_status_kind.normal:        -21,
pysvn.wc_status_kind.external:      -21,

# uncontrolled but interesting files
pysvn.wc_status_kind.unversioned:   -22,

# uncontrolled but uninteresting files
pysvn.wc_status_kind.ignored:       -23,

# svn will not return these as the status of a file only of a change in a file
pysvn.wc_status_kind.replaced:      0,
pysvn.wc_status_kind.none:          0,
pysvn.wc_status_kind.merged:        0,
}

prop_sort_offset = 10

def wcNotifyActionLookup( action ):
    if action in wc_notify_action_map:
        return wc_notify_action_map[ action ]

    return repr( action )

wc_notify_action_map = {
    pysvn.wc_notify_action.add: 'A',
    pysvn.wc_notify_action.annotate_revision: 'a',
    pysvn.wc_notify_action.commit_added: 'A',
    pysvn.wc_notify_action.commit_copied: 'commit_copied',
    pysvn.wc_notify_action.commit_copied_replaced: 'commit_copied_replaced',
    pysvn.wc_notify_action.commit_deleted: 'D',
    pysvn.wc_notify_action.commit_modified: 'M',
    pysvn.wc_notify_action.commit_postfix_txdelta: None,
    pysvn.wc_notify_action.commit_replaced: 'R',
    pysvn.wc_notify_action.commit_finalizing: None,
    pysvn.wc_notify_action.copy: 'c',
    pysvn.wc_notify_action.delete: 'D',
    pysvn.wc_notify_action.exclude: 'exclude',
    pysvn.wc_notify_action.failed_conflict: 'failed_conflict',
    pysvn.wc_notify_action.failed_external: 'failed_external',
    pysvn.wc_notify_action.failed_forbidden_by_server: 'failed_forbidden_by_server',
    pysvn.wc_notify_action.failed_lock: 'lock failed',
    pysvn.wc_notify_action.failed_locked: 'failed_locked',
    pysvn.wc_notify_action.failed_missing: 'failed_missing',
    pysvn.wc_notify_action.failed_no_parent: 'failed_no_parent',
    pysvn.wc_notify_action.failed_out_of_date: 'failed_out_of_date',
    pysvn.wc_notify_action.failed_revert: 'F',
    pysvn.wc_notify_action.failed_unlock: 'unlock failed',
    pysvn.wc_notify_action.locked: 'Locked',
    pysvn.wc_notify_action.merge_completed: 'merge_completed',
    pysvn.wc_notify_action.merge_elide_info: 'merge_elide_info',
    pysvn.wc_notify_action.merge_record_info: 'merge_record_info',
    pysvn.wc_notify_action.merge_record_info_begin: 'merge_record_info_begin',
    pysvn.wc_notify_action.patch: 'patch',
    pysvn.wc_notify_action.patch_applied_hunk: 'patch_applied_hunk',
    pysvn.wc_notify_action.patch_hunk_already_applied: 'patch_hunk_already_applied',
    pysvn.wc_notify_action.patch_rejected_hunk: 'patch_rejected_hunk',
    pysvn.wc_notify_action.path_nonexistent: 'path_nonexistent',
    pysvn.wc_notify_action.property_added: '_A',
    pysvn.wc_notify_action.property_deleted: '_D',
    pysvn.wc_notify_action.property_deleted_nonexistent: 'property_deleted_nonexistent',
    pysvn.wc_notify_action.property_modified: '_M',
    pysvn.wc_notify_action.resolved: 'R',
    pysvn.wc_notify_action.restore: 'R',
    pysvn.wc_notify_action.revert: 'R',
    pysvn.wc_notify_action.revprop_deleted: 'revprop_deleted',
    pysvn.wc_notify_action.revprop_set: 'revprop_set',
    pysvn.wc_notify_action.skip: '?',
    pysvn.wc_notify_action.skip_conflicted: 'skip_conflicted',
    pysvn.wc_notify_action.tree_conflict: 'tree_conflict',
    pysvn.wc_notify_action.unlocked: 'Unlocked',
    pysvn.wc_notify_action.update_add: 'A',
    pysvn.wc_notify_action.update_completed: None,
    pysvn.wc_notify_action.update_delete: 'D',
    pysvn.wc_notify_action.update_external: 'E',
    pysvn.wc_notify_action.update_external_removed: 'update_external_removed',
    pysvn.wc_notify_action.update_shadowed_add: 'update_shadowed_add',
    pysvn.wc_notify_action.update_shadowed_delete: 'update_shadowed_delete',
    pysvn.wc_notify_action.update_shadowed_update: 'update_shadowed_update',
    pysvn.wc_notify_action.update_skip_obstruction: 'update_skip_obstruction',
    pysvn.wc_notify_action.update_skip_working_only: 'update_skip_working_only',
    pysvn.wc_notify_action.update_started: 'update_started',
    pysvn.wc_notify_action.update_update: 'U',
    pysvn.wc_notify_action.upgraded_path: 'upgraded_path',
    pysvn.wc_notify_action.upgraded_path: 'upgraded_path',
    pysvn.wc_notify_action.url_redirect: 'url_redirect',
    }

def wcNotifyTypeLookup( action ):
    if action in wc_notify_type_map:
        return wc_notify_type_map[ action ]

    return repr(action)

wc_notify_type_map = {
    pysvn.wc_notify_action.add: 'A',
    pysvn.wc_notify_action.annotate_revision: 'A',
    pysvn.wc_notify_action.commit_added: 'C',
    pysvn.wc_notify_action.commit_copied: None,
    pysvn.wc_notify_action.commit_copied_replaced: None,
    pysvn.wc_notify_action.commit_deleted: 'C',
    pysvn.wc_notify_action.commit_modified: 'C',
    pysvn.wc_notify_action.commit_finalizing: None,
    pysvn.wc_notify_action.commit_postfix_txdelta: None,
    pysvn.wc_notify_action.commit_replaced: 'C',
    pysvn.wc_notify_action.copy: 'A',
    pysvn.wc_notify_action.delete: 'A',
    pysvn.wc_notify_action.exclude: None,
    pysvn.wc_notify_action.failed_conflict: '?',
    pysvn.wc_notify_action.failed_external: None,
    pysvn.wc_notify_action.failed_forbidden_by_server: '?',
    pysvn.wc_notify_action.failed_lock: None,
    pysvn.wc_notify_action.failed_locked: '?',
    pysvn.wc_notify_action.failed_missing: '?',
    pysvn.wc_notify_action.failed_no_parent: '?',
    pysvn.wc_notify_action.failed_out_of_date: '?',
    pysvn.wc_notify_action.failed_revert: 'A',
    pysvn.wc_notify_action.failed_unlock: None,
    pysvn.wc_notify_action.locked: None,
    pysvn.wc_notify_action.merge_completed: None,
    pysvn.wc_notify_action.merge_elide_info: None,
    pysvn.wc_notify_action.merge_record_info: None,
    pysvn.wc_notify_action.merge_record_info_begin: None,
    pysvn.wc_notify_action.patch: None,
    pysvn.wc_notify_action.patch_applied_hunk: None,
    pysvn.wc_notify_action.patch_hunk_already_applied: None,
    pysvn.wc_notify_action.patch_rejected_hunk: None,
    pysvn.wc_notify_action.path_nonexistent: None,
    pysvn.wc_notify_action.property_added: 'A',
    pysvn.wc_notify_action.property_deleted: 'D',
    pysvn.wc_notify_action.property_deleted_nonexistent: None,
    pysvn.wc_notify_action.property_modified: 'M',
    pysvn.wc_notify_action.resolved: 'A',
    pysvn.wc_notify_action.restore: 'A',
    pysvn.wc_notify_action.revert: 'A',
    pysvn.wc_notify_action.revprop_deleted: None,
    pysvn.wc_notify_action.revprop_set: None,
    pysvn.wc_notify_action.skip: '?',
    pysvn.wc_notify_action.skip_conflicted: '?',
    pysvn.wc_notify_action.status_completed: None,
    pysvn.wc_notify_action.status_external: None,
    pysvn.wc_notify_action.tree_conflict: None,
    pysvn.wc_notify_action.unlocked: None,
    pysvn.wc_notify_action.update_add: 'U',
    pysvn.wc_notify_action.update_completed: None,
    pysvn.wc_notify_action.update_delete: 'U',
    pysvn.wc_notify_action.update_external: 'U',
    pysvn.wc_notify_action.update_external_removed: None,
    pysvn.wc_notify_action.update_shadowed_add: None,
    pysvn.wc_notify_action.update_shadowed_delete: None,
    pysvn.wc_notify_action.update_shadowed_update: None,
    pysvn.wc_notify_action.update_skip_obstruction: None,
    pysvn.wc_notify_action.update_skip_working_only: None,
    pysvn.wc_notify_action.update_started: None,
    pysvn.wc_notify_action.update_update: 'U',
    pysvn.wc_notify_action.upgraded_path: None,
    pysvn.wc_notify_action.upgraded_path: None,
    pysvn.wc_notify_action.url_redirect: None,
    }

#
#    format the concise status from file
#
def svnStatusFormat( state ):
    if state is None:
        return ''

    if state.node_status == pysvn.wc_status_kind.modified:
        node_code = wc_status_kind_map[ state.text_status ]
    else:
        node_code = wc_status_kind_map[ state.node_status ]

    prop_code = wc_status_kind_map[ state.prop_status ]

    if node_code == ' ' and prop_code != ' ':
        node_code = '_'

    if (state.is_copied or state.is_switched) and prop_code == ' ':
        prop_code = '_'

    lock_state = 'K' if state.lock is not None else ' '
    state = '%s%s%s%s%s%s' % (node_code, prop_code,
            ' L'[ state.wc_is_locked ],
            ' +'[ state.is_copied ],
            ' S'[ state.is_switched ],
            lock_state)

    return state.strip()
