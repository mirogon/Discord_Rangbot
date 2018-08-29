import discord
import os
import copy
import time
import asyncio
import threading
import pickle

client = discord.Client()
memberlock = threading.Lock()


class Member:
		
	def __init__(self, dm):
			self.discord_member = dm
	
	discord_member = discord.Member
	collected_points = 0
	rank = ""
	is_online = True
	new_rank = False
	
def get_saved_members():
	sm = []
	if os.path.getsize("members.pickle") > 0:
		with open("members.pickle", "rb") as handle:
			sm = pickle.load(handle)
			handle.close()
	return sm

def save_members(members):

	m = copy.deepcopy(members)

	for i in m:
		i.is_online = False
	with open("members.pickle", "wb") as handle:
		pickle.dump(m, handle, protocol=pickle.HIGHEST_PROTOCOL)
		handle.close()
        

def backup_save(members):

	f = open("baksave.pickle", "w");
	for m in members:
		f.write("name: ")
		f.write(str(m.discord_member.name))
		f.write(" points: ")
		f.write(str(m.collected_points))
		f.write("\n")
	f.close()

def determine_rank(points):

		if points < 900:
			return "Reisender"
		elif points >= 900 and points < 1800:
			return "Aufsteigender"
		elif points >= 1800 and points < 2700:
			return "Hüter"
		elif points >= 2700 and points < 5400:
			return "Gildenhüter"
		elif points >= 5400 and points < 10800:
			return "Drachenjäger"
		elif points >= 10800 and points < 21600:
			return "Drachenkönig"
		elif points >= 21600 and points < 60000:
			return "Kriegsgott"
		elif points >= 60000 :
			return "Erzengel"
		else:
			return "Reisender"
			
def next_rank_percentage(points):
		if points < 900:
			lp = int( 100 - ( (points/900) * 100 ) )
			msg = "Dir fehlt noch " + str(lp) + "% bis zum nächsten Rang Aufsteigender"
			return msg
		elif points >= 900 and points < 1800:
			lp =  int( 100 - ((points/1800) * 100) )
			msg = "Dir fehlt noch " + str(lp) + "% bis zum nächsten Rang Hüter"
			return msg
		elif points >= 1800 and points < 2700:
			lp =  int( 100 - ((points/2700) * 100) )
			msg = "Dir fehlt noch "+ str(lp) + "% bis zum nächsten Rang Gildenhüter"
			return msg
		elif points >= 2700 and points < 5400:
			lp = int( 100 - ((points/12000) * 100) )
			msg = "Dir fehlt noch " + str(lp) + "% bis zum nächsten Rang Drachenjäger"
			return msg
		elif points >= 5400 and points < 10800:
			lp = int( 100 - ((points/15000) * 100) )
			msg = "Dir fehlt noch " + str(lp) + "% bis zum nächsten Rang Drachenkönig"
			return msg
		elif points >= 10800 and points < 21600:
			lp = int( 100 - ((points/18000) * 100) )
			msg = "Dir fehlt noch " + str(lp) + "% bis zum nächsten Rang Kriegsgott"
			return msg
		elif points >= 21600 and points < 60000:
			lp = int( 100 - ((points/24000) * 100) )
			msg = "Dir fehlt noch " + str(lp) + "% bis zum nächsten Rang Erzengel"
			return msg
		elif points >= 60000 :
			msg = "Du bist ein Erzengel, es gibt keinen Rang über dir!"
			return msg

def set_rank(member):	
	new_rank = determine_rank(member.collected_points)

	if new_rank != member.rank:
		memberlock.acquire()
		member.new_rank = True
		member.rank = new_rank
		memberlock.release()
		print("Hurra, ", member.discord_member.name, " ist nun ", new_rank, ".")

def collect_points(members):
	lt = time.clock()
	while not client.is_closed:
		
		if (time.clock() - lt) >= 60:
			print("collecting points")
			for m in members:
				if m.is_online == True:
					print(m.discord_member.name, " collected a point.", " He now has: ", m.collected_points)
					memberlock.acquire()
					m.collected_points += 1
					memberlock.release()
					set_rank(m)
					
			save_members(members)
			backup_save(members)
			lt = time.clock()
					
members_ = get_saved_members()

@client.event
async def on_message(message):
	print("received message")
	if message.author == client.user:
		return
		
	if message.content.startswith("!rang"):
		print("received !rang")
		for m in members_:
			print("memberid: ", m.discord_member.name)
			print("authorid: ", message.author.name)
			if m.discord_member.id == message.author.id:
				msg = m.discord_member.name + " hat zurzeit " + str(m.collected_points) + " Punkte"
				await client.send_message(message.channel, msg)
				msg2 = next_rank_percentage(m.collected_points)
				await client.send_message(message.channel, msg2)

@client.event
async def on_voice_state_update(before, after):
	print("member update")
	
	#set all members offline
	memberlock.acquire()
	for m in members_:
		m.is_online = False
	memberlock.release()
	
	already_created = False
	
	#apply new roles
	for m in members_:
		if m.new_rank == True:
			m.new_rank = False
			for server in client.servers:
				for role in server.roles:
					if m.rank == role.name:
						await client.add_roles(m.discord_member, role)
	
	#create new member and check whos online
	for server in client.servers:
		for channel in server.channels:
			for vm in channel.voice_members:
				already_created = False
				for m in members_:
					if m.discord_member.id == vm.id:
					
						already_created = True
						print(m.discord_member.name, " is online")
						
						memberlock.acquire()
						m.discord_member = vm
						if channel.name != "AFK":
							m.is_online = True
						memberlock.release()
				
				if already_created == False:
					memberlock.acquire()
					members_.append(Member(vm))
					memberlock.release()
					print("created member ", vm.name)

collect_thread = threading.Thread(target=collect_points, args=(members_,))		
collect_thread.start()

client.run("NDgzMzE3MzE1ODE1ODY2Mzc4.DmRsEA.JACqlxMg0kt4Oj0JyPNVRuaMNT0")
