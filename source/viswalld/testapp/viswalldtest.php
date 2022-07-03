<?php
    $MSGKEY_WRITE = 650001;
    $MSGKEY_READ = 650002;

    $msg_id_write = msg_get_queue ($MSGKEY_WRITE);
    $msg_id_read = msg_get_queue ($MSGKEY_READ);

    if (!msg_send ($msg_id_write, 1, $argv[1], false, false, $msg_err))
        echo "Msg not sent because $msg_err\n";

    while (1) {
        if (msg_receive ($msg_id_read, 0, $msg_type, 16384, $msg, false, 0, $msg_error)) {
            echo "$msg\n";
            break;
        } else {
            echo "Received $msg_error fetching message\n";
            break;
        }
    }

    echo "Executed: ".$argv[1]."\n";
?>
