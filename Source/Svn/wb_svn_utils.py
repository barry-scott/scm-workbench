'''
 ====================================================================
 Copyright (c) 2003-2016 Barry A Scott.  All rights reserved.

 This software is licensed as described in the file LICENSE.txt,
 which you should have received as part of this distribution.

 ====================================================================

    wb_svn_utils.py

'''
import pysvn
import time
import locale

class SvnVersionInfo:
    #
    # Keep infos about the features of the available pysvn version
    #
    def __init__(self):
        self.notify_action_has_failed_lock = hasattr( pysvn.wc_notify_action, 'failed_lock' )
        self.has_depth = hasattr( pysvn, 'depth' )
        self.notify_action_has_property_events = hasattr( pysvn.wc_notify_action, 'property_added' )
        self.notify_action_has_upgrade_events = hasattr( pysvn.wc_notify_action, 'upgraded_path' )
        self.has_upgrade = self.notify_action_has_upgrade_events

version_info = SvnVersionInfo()

def fmtDateTime( val ):
    encoding = locale.getlocale()[1]
    if type( val ) == float:
        val = time.localtime( val )

    return time.strftime( '%d-%b-%Y %H:%M:%S', val )

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
    pysvn.wc_notify_action.commit_added: 'A',
    pysvn.wc_notify_action.commit_deleted: 'D',
    pysvn.wc_notify_action.commit_modified: 'M',
    pysvn.wc_notify_action.commit_postfix_txdelta: None,
    pysvn.wc_notify_action.commit_replaced: 'R',
    pysvn.wc_notify_action.copy: 'c',
    pysvn.wc_notify_action.delete: 'D',
    pysvn.wc_notify_action.failed_revert: 'F',
    pysvn.wc_notify_action.resolved: 'R',
    pysvn.wc_notify_action.restore: 'R',
    pysvn.wc_notify_action.revert: 'R',
    pysvn.wc_notify_action.skip: '?',
    pysvn.wc_notify_action.status_completed: None,
    pysvn.wc_notify_action.status_external: 'E',
    pysvn.wc_notify_action.update_add: 'A',
    pysvn.wc_notify_action.update_completed: None,
    pysvn.wc_notify_action.update_delete: 'D',
    pysvn.wc_notify_action.update_external: 'E',
    pysvn.wc_notify_action.update_update: 'U',
    pysvn.wc_notify_action.annotate_revision: 'a',
    }

if version_info.notify_action_has_failed_lock:
    wc_notify_action_map[ pysvn.wc_notify_action.failed_lock ] = 'lock failed'
    wc_notify_action_map[ pysvn.wc_notify_action.failed_unlock ] = 'unlock failed'
    wc_notify_action_map[ pysvn.wc_notify_action.locked ] = 'Locked'
    wc_notify_action_map[ pysvn.wc_notify_action.unlocked ] = 'Unlocked'

if version_info.notify_action_has_property_events:
    wc_notify_action_map[ pysvn.wc_notify_action.property_added ] = '_A'
    wc_notify_action_map[ pysvn.wc_notify_action.property_modified ] = '_M'
    wc_notify_action_map[ pysvn.wc_notify_action.property_deleted ] = '_D'
    wc_notify_action_map[ pysvn.wc_notify_action.property_deleted_nonexistent ] = 'property_deleted_nonexistent'
    wc_notify_action_map[ pysvn.wc_notify_action.revprop_set ] = 'revprop_set'
    wc_notify_action_map[ pysvn.wc_notify_action.revprop_deleted ] = 'revprop_deleted'
    wc_notify_action_map[ pysvn.wc_notify_action.merge_completed ] = 'merge_completed'
    wc_notify_action_map[ pysvn.wc_notify_action.tree_conflict ] = 'tree_conflict'
    wc_notify_action_map[ pysvn.wc_notify_action.failed_external ] = 'failed_external'

if version_info.notify_action_has_upgrade_events:
    wc_notify_action_map[ pysvn.wc_notify_action.upgraded_path ] = 'upgraded_path'
    wc_notify_action_map[ pysvn.wc_notify_action.update_started ] = "update_started"
    wc_notify_action_map[ pysvn.wc_notify_action.update_skip_obstruction ] = "update_skip_obstruction"
    wc_notify_action_map[ pysvn.wc_notify_action.update_skip_working_only ] = "update_skip_working_only"
    wc_notify_action_map[ pysvn.wc_notify_action.update_external_removed ] = "update_external_removed"
    wc_notify_action_map[ pysvn.wc_notify_action.update_shadowed_add ] = "update_shadowed_add"
    wc_notify_action_map[ pysvn.wc_notify_action.update_shadowed_update ] = "update_shadowed_update"
    wc_notify_action_map[ pysvn.wc_notify_action.update_shadowed_delete ] = "update_shadowed_delete"
    wc_notify_action_map[ pysvn.wc_notify_action.merge_record_info ] = "merge_record_info"
    wc_notify_action_map[ pysvn.wc_notify_action.upgraded_path ] = "upgraded_path"
    wc_notify_action_map[ pysvn.wc_notify_action.merge_record_info_begin ] = "merge_record_info_begin"
    wc_notify_action_map[ pysvn.wc_notify_action.merge_elide_info ] = "merge_elide_info"
    wc_notify_action_map[ pysvn.wc_notify_action.patch ] = "patch"
    wc_notify_action_map[ pysvn.wc_notify_action.patch_applied_hunk ] = "patch_applied_hunk"
    wc_notify_action_map[ pysvn.wc_notify_action.patch_rejected_hunk ] = "patch_rejected_hunk"
    wc_notify_action_map[ pysvn.wc_notify_action.patch_hunk_already_applied ] = "patch_hunk_already_applied"
    wc_notify_action_map[ pysvn.wc_notify_action.commit_copied ] = "commit_copied"
    wc_notify_action_map[ pysvn.wc_notify_action.commit_copied_replaced ] = "commit_copied_replaced"
    wc_notify_action_map[ pysvn.wc_notify_action.url_redirect ] = "url_redirect"
    wc_notify_action_map[ pysvn.wc_notify_action.path_nonexistent ] = "path_nonexistent"
    wc_notify_action_map[ pysvn.wc_notify_action.exclude ] = "exclude"
    wc_notify_action_map[ pysvn.wc_notify_action.failed_conflict ] = "failed_conflict"
    wc_notify_action_map[ pysvn.wc_notify_action.failed_missing ] = "failed_missing"
    wc_notify_action_map[ pysvn.wc_notify_action.failed_out_of_date ] = "failed_out_of_date"
    wc_notify_action_map[ pysvn.wc_notify_action.failed_no_parent ] = "failed_no_parent"
    wc_notify_action_map[ pysvn.wc_notify_action.failed_locked ] = "failed_locked"
    wc_notify_action_map[ pysvn.wc_notify_action.failed_forbidden_by_server ] = "failed_forbidden_by_server"
    wc_notify_action_map[ pysvn.wc_notify_action.skip_conflicted ] = "skip_conflicted"

def wcNotifyTypeLookup( action ):
    if action in wc_notify_type_map:
        return wc_notify_type_map[ action ]

    return '?'

wc_notify_type_map = {
    pysvn.wc_notify_action.add: 'A',
    pysvn.wc_notify_action.commit_added: 'C',
    pysvn.wc_notify_action.commit_deleted: 'C',
    pysvn.wc_notify_action.commit_modified: 'C',
    pysvn.wc_notify_action.commit_postfix_txdelta: None,
    pysvn.wc_notify_action.commit_replaced: 'C',
    pysvn.wc_notify_action.copy: 'A',
    pysvn.wc_notify_action.delete: 'A',
    pysvn.wc_notify_action.failed_revert: 'A',
    pysvn.wc_notify_action.resolved: 'A',
    pysvn.wc_notify_action.restore: 'A',
    pysvn.wc_notify_action.revert: 'A',
    pysvn.wc_notify_action.skip: '?',
    pysvn.wc_notify_action.status_completed: None,
    pysvn.wc_notify_action.status_external: 'A',
    pysvn.wc_notify_action.update_add: 'U',
    pysvn.wc_notify_action.update_completed: None,
    pysvn.wc_notify_action.update_delete: 'U',
    pysvn.wc_notify_action.update_external: 'U',
    pysvn.wc_notify_action.update_update: 'U',
    pysvn.wc_notify_action.annotate_revision: 'A',
    }

if version_info.notify_action_has_failed_lock:
    wc_notify_type_map[ pysvn.wc_notify_action.failed_lock ] = None
    wc_notify_type_map[ pysvn.wc_notify_action.failed_unlock ] = None
    wc_notify_type_map[ pysvn.wc_notify_action.locked ] = None
    wc_notify_type_map[ pysvn.wc_notify_action.unlocked ] = None

if version_info.notify_action_has_property_events:
    wc_notify_type_map[ pysvn.wc_notify_action.property_added ] = 'A'
    wc_notify_type_map[ pysvn.wc_notify_action.property_modified ] = 'M'
    wc_notify_type_map[ pysvn.wc_notify_action.property_deleted ] = 'D'
    wc_notify_type_map[ pysvn.wc_notify_action.property_deleted_nonexistent ] = None
    wc_notify_type_map[ pysvn.wc_notify_action.revprop_set ] = None
    wc_notify_type_map[ pysvn.wc_notify_action.revprop_deleted ] = None
    wc_notify_type_map[ pysvn.wc_notify_action.merge_completed ] = None
    wc_notify_type_map[ pysvn.wc_notify_action.tree_conflict ] = None
    wc_notify_type_map[ pysvn.wc_notify_action.failed_external ] = None

if version_info.notify_action_has_upgrade_events:
    wc_notify_type_map[ pysvn.wc_notify_action.upgraded_path ] = None
    wc_notify_type_map[ pysvn.wc_notify_action.update_started ] = None
    wc_notify_type_map[ pysvn.wc_notify_action.update_skip_obstruction ] = None
    wc_notify_type_map[ pysvn.wc_notify_action.update_skip_working_only ] = None
    wc_notify_type_map[ pysvn.wc_notify_action.update_external_removed ] = None
    wc_notify_type_map[ pysvn.wc_notify_action.update_shadowed_add ] = None
    wc_notify_type_map[ pysvn.wc_notify_action.update_shadowed_update ] = None
    wc_notify_type_map[ pysvn.wc_notify_action.update_shadowed_delete ] = None
    wc_notify_type_map[ pysvn.wc_notify_action.merge_record_info ] = None
    wc_notify_type_map[ pysvn.wc_notify_action.upgraded_path ] = None
    wc_notify_type_map[ pysvn.wc_notify_action.merge_record_info_begin ] = None
    wc_notify_type_map[ pysvn.wc_notify_action.merge_elide_info ] = None
    wc_notify_type_map[ pysvn.wc_notify_action.patch ] = None
    wc_notify_type_map[ pysvn.wc_notify_action.patch_applied_hunk ] = None
    wc_notify_type_map[ pysvn.wc_notify_action.patch_rejected_hunk ] = None
    wc_notify_type_map[ pysvn.wc_notify_action.patch_hunk_already_applied ] = None
    wc_notify_type_map[ pysvn.wc_notify_action.commit_copied ] = None
    wc_notify_type_map[ pysvn.wc_notify_action.commit_copied_replaced ] = None
    wc_notify_type_map[ pysvn.wc_notify_action.url_redirect ] = None
    wc_notify_type_map[ pysvn.wc_notify_action.path_nonexistent ] = None
    wc_notify_type_map[ pysvn.wc_notify_action.exclude ] = None
    wc_notify_type_map[ pysvn.wc_notify_action.failed_conflict ] = '?'
    wc_notify_type_map[ pysvn.wc_notify_action.failed_missing ] = '?'
    wc_notify_type_map[ pysvn.wc_notify_action.failed_out_of_date ] = '?'
    wc_notify_type_map[ pysvn.wc_notify_action.failed_no_parent ] = '?'
    wc_notify_type_map[ pysvn.wc_notify_action.failed_locked ] = '?'
    wc_notify_type_map[ pysvn.wc_notify_action.failed_forbidden_by_server ] = '?'
    wc_notify_type_map[ pysvn.wc_notify_action.skip_conflicted ] = '?'

#
#    format the concise status from file
#
def svnStatusFormat( state ):
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
