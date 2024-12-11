from shared_data.shared_data import bot


@bot.callback_query_handler(func=lambda call: call.data == "dismiss_message")
def dismiss_message(call):
    """
    dismiss button
    """
    try:
        bot.delete_message(call.message.chat.id, call.message.message_id)
    except Exception as e:
        bot.answer_callback_query(call.id, "Unable to delete the message.")
