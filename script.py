# encoding: utf8
import sqlite3
import configparser
import os
import re
import getpass
import sys
import time
import datetime
import logging
import asyncio
from telethon import TelegramClient, events

from telethon.tl.types import *
from telethon.tl.functions.channels import EditBannedRequest,DeleteMessagesRequest
from telethon.tl.functions.messages import SendMessageRequest, EditMessageRequest
from telethon.tl.functions.users import GetFullUserRequest
from telethon.tl.functions.messages import ImportChatInviteRequest
from telethon.tl.functions.messages import CheckChatInviteRequest

API_ID = None
API_HASH = None
CLIENT = None
CONN = None
CURSOR = None
CRAWL = False

def extract_configs():
    global API_ID, API_HASH
    config = configparser.ConfigParser()
    try:
        config.read('config.ini')
        if config.has_section('API')==False:
            print("Creating a new .ini file...")
            config.add_section('API')
            id_input = input("Please enter your API's id: ")
            hash_input = input("Please enter your API's hash: ")
            config.set('API', 'id', id_input)
            config.set('API', 'hash', hash_input)
            config.add_section('SETTINGS')
            config.set('SETTINGS', 'crawl', "0")       # join every invite link if finds
            print("Writing config.ini...")
            config.write(open('config.ini', 'w'))
        API_ID = config.getint('API', 'id')
        API_HASH = config.get('API', 'hash')
    except Exception as e:
        print(e)

def setup_telegram_connection():
    global CLIENT
    print("Setting up Telegram connection...")
    CLIENT = TelegramClient('anon', API_ID, API_HASH)

def setup_sqlite_connection(path_to_file):
    global CONN, CURSOR
    try:
        print("Setting up SQLITE3 connection...")
        CONN = sqlite3.connect(path_to_file, check_same_thread=False)
        CURSOR = CONN.cursor()
        CURSOR.execute("CREATE TABLE IF NOT EXISTS UserUpdates ('id' INTEGER, 'username' TEXT, 'first_name' TEXT, 'second_name' TEXT, 'update' TEXT, 'date' TEXT)")
        CURSOR.execute("CREATE TABLE IF NOT EXISTS Messages ( 'id' INTEGER, 'to_id' INTEGER, 'date' TEXT, 'message' INTEGER, 'out' INTEGER, 'mentioned' INTEGER, 'media_unread' INTEGER, 'silent' INTEGER, 'post' INTEGER, 'from_id' INTEGER, 'fwd_from' INTEGER, 'via_bot_id' INTEGER, 'reply_to_msg_id' INTEGER, 'media' INTEGER, 'reply_markup' INTEGER, 'entities' INTEGER, 'views' INTEGER, 'edit_date' TEXT, 'post_author' INTEGER, 'grouped_id' INTEGER, 'edited' INTEGER, 'deleted' INTEGER )")
        CURSOR.execute("CREATE TABLE IF NOT EXISTS ChatActions ( 'id' INTEGER, 'to_id' INTEGER,  'date' TEXT, 'event_name' TEXT, 'domain' TEXT, 'title' TEXT, 'chat_id' TEXT, 'users' TEXT, 'user_id' INTEGER, 'channel_id' INTEGER, 'message' TEXT, 'game_id' INTEGER, 'score' INTEGER, 'currency' TEXT, 'total_amount' INTEGER, 'call_id' INTEGER, 'reason' TEXT, 'duration' INTEGER, 'values' TEXT, 'credentials' TEXT, 'photo' TEXT, 'inviter_id' INTEGER, 'payload' TEXT, 'charge' TEXT, 'info' TEXT, 'shipping_option_id' TEXT, 'types' TEXT )")
        CURSOR.execute("CREATE TABLE IF NOT EXISTS Joined ( 'id' INTEGER, 'from_id' INTEGER, 'hash' TEXT, 'title' TEXT, 'patricipants_count' INTEGER, 'version' INTEGER, 'creator' INTEGER, 'admins_enabled' INTEGER, 'admin' INTEGER, 'deactivated' INTEGER, 'migrated_to' INTEGER, 'date' TEXT )")
        CURSOR.execute("CREATE TABLE IF NOT EXISTS Edited ( 'id' INTEGER, 'to_id' INTEGER, 'from_id' INTEGER, 'message' TEXT, 'date' TEXT )")
        CURSOR.execute("CREATE TABLE IF NOT EXISTS Deleted ( 'id' INTEGER, 'to_id' INTEGER, 'date' TEXT )")
    except Exception as e:
        print(e)

async def join_via_link(text, client):
    start = text.index("t.me/joinchat/") + 14
    hash = text[start:start+22]
    #chat_invite = await client(CheckChatInviteRequest(hash))
    result = await client(ImportChatInviteRequest(hash))
    print(result)
    link = text[text.index("t.me/joinchat/"):text.index("t.me/joinchat/")+36]
    result = await client.get_entity(link)
    id = result.id
    title = result.title
    participants_count = result.participants_count
    version = result.version
    created = result.created
    admins_enabled = result.admins_enabled
    admin = result.admin
    deactivated = result.deactivated
    migrated_to = result.migrated.to

async def record_message(message, client):
    try:
        message_id = message.id
        date = message.date.strftime('%Y.%d.%m %H:%M:%S %a')
        to_id = list(message.to_id.__dict__.values())[0]
        text = message.message
        if "t.me/joinchat" in text and CRAWL == True:
            await join_via_link(text, client)
        out = message.out
        mentioned = message.mentioned
        media_unread = message.media_unread
        silent = message.silent
        post = message.post
        from_id = message.from_id
        fwd_from = None
        via_bot_id = message.via_bot_id
        reply_to_msg_id = message.reply_to_msg_id
        media = None
        reply_markup = None
        entities = None
        views = message.views
        edit_date = message.edit_date
        post_author = message.post_author
        grouped_id = message.grouped_id
        CURSOR.execute("INSERT INTO Messages VALUES (:id, :to_id, :date, :message, :out, :mentioned, :media_unread, :silent, :post, :from_id, :fwd_from, :via_bot_id, :reply_to_msg_id, :media, :reply_markup, :entities, :views, :edit_date, :post_author, :grouped_id, :edited, :deleted)",
           {'id':message_id, 'to_id':to_id, 'date':date, 'message':text,
            'out':out, 'mentioned':mentioned, 'media_unread':media_unread, 'silent':silent,
            'post':post, 'from_id':from_id, 'fwd_from':fwd_from, 'via_bot_id':via_bot_id, 'reply_to_msg_id':reply_to_msg_id,
            'media':media, 'reply_markup':reply_markup, 'entities':entities, 'views':views,
            'edit_date':edit_date, 'post_author':post_author, 'grouped_id':grouped_id, 'edited':0, 'deleted':0,})
        CONN.commit()
    except Exception as e:
        print(e)

def main():
    logging.basicConfig(level=logging.ERROR)
    extract_configs()
    setup_telegram_connection()
    setup_sqlite_connection('logs.sqlite')

    @CLIENT.on(events.NewMessage())
    async def handlerNewMessage(event):
        try:
            await record_message(event.message, CLIENT)
        except KeyboardInterrupt:
            raise
        except Exception as e:
            print(e)

    @CLIENT.on(events.ChatAction())
    async def handlerChatAction(event):
        event_name = type(event.original_update.message.action).__name__
        date = event.original_update.message.date
        date = date.strftime('%Y.%d.%m %H:%M:%S %a')
        attributes = event.original_update.message.action.__dict__
        attributes['id']=event.original_update.message.id
        attributes['to_id']=list(event.original_update.message.to_id.__dict__.values())[0] ###########
        attributes['event_name']=event_name
        attributes['date'] = date
        for k, v in attributes.items():
            if type(v)==list:
                attributes[k] = str(v)
        columns = ','.join(str(e) for e in list(attributes.keys()))
        placeholders = ':'+', :'.join(str(e) for e in list(attributes.keys()))
        CURSOR.execute("INSERT INTO ChatActions (%s) VALUES (%s)" % (columns, placeholders), attributes)
        CONN.commit()

    @CLIENT.on(events.MessageEdited())
    async def handlerMessageEdited(event):
        _id = event.message.id
        _to_id = list(event.message.to_id.__dict__.values())[0]
        _from_id = event.message.from_id
        _message = event.message.message
        _date = event.message.date.strftime('%Y.%d.%m %H:%M:%S %a')
        CURSOR.execute("UPDATE Messages SET edited=1 WHERE to_id=:to_id AND id=:id", {'id':_id,'to_id':_to_id})
        CURSOR.execute("INSERT INTO Edited VALUES (:id, :to_id, :from_id, :message, :date)", {'id':_id,'to_id':_to_id,'from_id':_from_id,'message':_message,'date':_date})
        CONN.commit()

    @CLIENT.on(events.MessageDeleted())
    async def handlerMessageDeleted(event):
        print(event)
        for i in range(len(event.deleted_ids)):
            attributes = []
            values = []
            attributes.append("id="+str(event.deleted_ids[i]))
            values.append(str(event.deleted_ids[i]))
            if isinstance(event.original_update, UpdateDeleteChannelMessages):
                attributes.append("to_id="+str(event.original_update.channel_id))
                values.append(str(event.original_update.channel_id))
            
            CURSOR.execute("UPDATE Messages SET deleted=1 WHERE %s" % ' AND '.join(attributes))
        #for i in range(len(event.deleted_ids)):
            current_time = datetime.datetime.now()
            values.append(current_time.strftime('"%Y.%d.%m %H:%M:%S %a"'))
            CURSOR.execute("INSERT INTO Deleted VALUES (%s)" % ', '.join(values))
        CONN.commit()

    @CLIENT.on(events.UserUpdate())
    async def handlerUserUpdate(event):
        id = event.original_update.user_id
        try:
            user = (await CLIENT(GetFullUserRequest(await CLIENT.get_input_entity(id)))).user
            username = user.username
            first_name = user.first_name
            last_name = user.last_name
        except Exception as e:
            print(e)
            username = ""
            first_name = ""
            last_name = ""
        event_name = type(event.original_update).__name__
        attributes = event.original_update.status.__dict__
        if len(list(attributes.values())) > 0:
            date = list(attributes.values())[0]
        else:
            date = [0,0,0,0,0,0]
        date = date.strftime('%Y.%d.%m %H:%M:%S %a')
        CURSOR.execute(
            "INSERT INTO UserUpdates VALUES(:id, :username, :firstName, :lastName, :update, :date)",
            {'id': id, 'username': username, 'firstName': first_name, 'lastName': last_name, 'update': event_name,
             'date': date })
        CONN.commit()

    CLIENT.start()
    CLIENT.run_until_disconnected()
    CONN.close()


if __name__ == '__main__':
    main()
