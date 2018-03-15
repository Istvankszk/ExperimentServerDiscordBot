import discord, asyncio, random, time, numpy, datetime, heapq, os
client = discord.Client()

import configparser
config = configparser.ConfigParser()
config.read("SigmaDiscordBot.ini")	#read config

if config['main']['verbose'] == "False":
	verbose = False
else:
	verbose = True

@client.event
async def on_ready():
	print('Starting {} bot'.format(client.user.name))
	if not verbose: print(" >verbose false. No further messages will be sent")
	else: print(" >running verbose mode")
	
#Role updates
async def background_loop():
	global server, exp_channel
	await client.wait_until_ready()
	await asyncio.sleep(1)
	while not client.is_closed:
		if verbose: print("updating ranks")
		server = client.get_server(config['main']['server_id'])
		rl_top = discord.utils.get(server.roles, id = config['roles']['top_role_id'])
		rl_long = discord.utils.get(server.roles, id = config['roles']['long_role_id'])
		rl_admin = discord.utils.get(server.roles, id = config['roles']['admin_role_id'])
		exp_channel = server.get_channel(config['channels']['experiment_channel_id'])
		cre_channel = server.get_channel(config['channels']['creative_channel_id'])
		exp_messages = []; exp_top3 = [];
		async for log in client.logs_from(exp_channel, limit = int(config['main']['top_limit'])):
			exp_messages.append(log.author.id) 
		exp_usr_id, exp_cts = numpy.unique(exp_messages, return_counts=True) 
		
		i = 1; k = 1
		while (k < 4):
			tmp = exp_usr_id[exp_cts.tolist().index(heapq.nlargest(i, exp_cts)[-1])] #Don't ask.
			#tmp = exp_usr_id[exp_cts.tolist().index(sorted(exp_cts.tolist())[-i])] #w/o heapq 
			exp_cts[exp_cts.tolist().index(heapq.nlargest(i, exp_cts)[-1])] = 99999 #fixes shit
			if server.get_member(tmp) in server.members:
				if rl_admin not in server.get_member(tmp).roles:
					exp_top3.append(tmp)
					k += 1
					if verbose: print( " >top list {} - {}". format(k-1, server.get_member(tmp).display_name))
			i += 1
			
		for k in exp_usr_id:
			member = server.get_member(k)
			if member in server.members:
				if k in exp_top3 and rl_top not in member.roles and rl_admin not in member.roles:
					if verbose: print("adding role [top] for user [{}]".format(member.display_name))
					await client.add_roles(member, rl_top)
				if k not in exp_top3 and rl_top in member.roles or rl_top in member.roles and rl_admin in member.roles:
					if verbose: print("removing role [top] for user [{}]".format(member.display_name))
					await client.remove_roles(member, rl_top)

		exp_messages_days = [];
		async for log in client.logs_from(exp_channel, after = datetime.datetime.now() - datetime.timedelta(days=int(config['main']['top_days'])+1), limit=500):
			exp_messages_days.append(log.author.id)
		exp_usr_days, exp_cts_days = numpy.unique(exp_messages_days, return_counts=True)
		for k in range(0, len(exp_usr_days.tolist())):
			member = server.get_member(exp_usr_days[k])
			if verbose : print ( " >days - {} - {}".format(member.display_name, exp_cts_days[k]))
			if exp_cts_days[k] > int(config['main']['top_days'])-1 and rl_long not in member.roles:
				if verbose: print("adding role [rl_long] for user [{}]".format(member.display_name))
				await client.add_roles(member, rl_long)
			elif exp_cts_days[k] <= int(config['main']['top_days'])-1 and rl_long in member.roles:
				if verbose: print("removing role [rl_long] for user [{}]".format(member.display_name))
				await client.remove_roles(member, rl_long)
		if verbose: print(" >updating ranks complete. next update in {} hours".format(int(config['main']['update_interval'])/60/60)) 
		await asyncio.sleep(int(config['main']['update_interval'])) #sleep

client.loop.create_task(background_loop()) #start

@client.event
async def on_message(message):
	#main variables (id) 
	server = client.get_server(config['main']['server_id'])
	rl_top = discord.utils.get(server.roles, id = config['roles']['top_role_id'])
	rl_long = discord.utils.get(server.roles, id = config['roles']['long_role_id'])
	rl_admin = discord.utils.get(server.roles, id = config['roles']['admin_role_id'])
	exp_channel = server.get_channel(config['channels']['experiment_channel_id'])
	cre_channel = server.get_channel(config['channels']['creative_channel_id'])
	
	if message.content.startswith('!info'): #User info
		if verbose: print("info command from {}".format(message.author.display_name))
		await client.send_typing(message.channel) 			#While calculating, send typing
		global_user = server.get_member(message.author.id) 	#user as member object
		#experiment:
		exp_messages = []; exp_author_times = 0; exp_rank = ""; exp_user = 0; exp_total = 0; # all messages / Post number user, total
		async for log in client.logs_from(exp_channel, limit = int(config['main']['top_limit'])): #experiment log
			exp_messages.append(log.author.id)
			if log.author == message.author:
				exp_user += 1
			exp_total += 1
		exp_usr, exp_cts = numpy.unique(exp_messages, return_counts=True) #user and message count
		exp_top = ""
		
		i = 1; k = 1
		while (k < 4):
			tmp = exp_usr[exp_cts.tolist().index(heapq.nlargest(i, exp_cts)[-1])] #DON'T. ASK.
			
			if server.get_member(tmp) in server.members:
				if rl_admin not in server.get_member(tmp).roles:
					if verbose: print(" >" + server.get_member(tmp).display_name)
					
					ma = exp_cts.tolist().index(heapq.nlargest(i, exp_cts)[-1])
					exp_top = exp_top + "\n > {} - {} ({}%)".format(server.get_member(exp_usr[ma]).display_name, exp_cts[ma], int(round(exp_cts[ma]/exp_total*100,0)))
					if exp_usr[ma] == global_user.id:
						exp_rank = ", earning you the {} rank".format(rl_top.name)
						
					k += 1
			exp_cts[exp_cts.tolist().index(heapq.nlargest(i, exp_cts)[-1])] = 99999 #STILL FIXES SHIT
			i += 1
			
			
		async for log in client.logs_from(exp_channel, after = datetime.datetime.now() - datetime.timedelta(days=int(config['main']['top_days'])+1), limit=500):
			if log.author == message.author:
				exp_author_times += 1
		
		if exp_author_times > int(config['main']['top_days'])-1:
			exp_rank = exp_rank + ", you also posted every day for the last {} days, giving you the '[{}]' rank".format(config['main']['top_days'],rl_long.name)
		
		exp_stat = "You have {} total ({}% of all) submissions in #experiment{}.\n\nThe top 3 (non admin) submitters are: {}".format(exp_user, int(round(exp_user/exp_total*100,0)), exp_rank, exp_top)
		#creative:
		cre_user = 0; cre_sigma = 0; #user posts/sigma
		async for log in client.logs_from(cre_channel, limit=5000): #creative log
			if log.author == message.author:
				cre_user += 1
			if (log.reactions):#has reaction
				for k in log.reactions:
					if k.custom_emoji and log.author != message.author: #only add if not from user who posted
						cre_sigma += 1		
		cre_stat = "You posted {} times in #creative and received a total of {} sigma. This equals to a total of {} points.\n\nTo see how points are calculated and what you can use them for, type !help\n\nRanks are updated every so often.".format(cre_user, cre_sigma, cre_user*5 + cre_sigma*10)
		#embed - final message:
		embed = discord.Embed(title="User info - {}".format(global_user.display_name), desciption = "desc", type = "rich", color = global_user.top_role.color) #color from role
		embed.add_field(name=">Experiment", value=exp_stat, inline=False)
		embed.add_field(name=">Creative", value=cre_stat, inline=True)
		embed.set_thumbnail(url = message.author.avatar_url) #user profile pic
		#send:
		await client.send_message(message.channel, embed=embed)
		
	#Totally useless IstvanTECH branding message.
	elif message.content.startswith('!tech'):
		await client.send_message(message.channel, "```\n    ________________    _____    _   __    ____________________  __\n   /  _/ ___/_  __/ |  / /   |  / | / /   /_  __/ ____/ ____/ / / /\n   / / \__ \ / /  | | / / /| | /  |/ /_____/ / / __/ / /   / /_/ /\n _/ / ___/ // /   | |/ / ___ |/ /|  /_____/ / / /___/ /___/ __  /\n/___//____//_/    |___/_/  |_/_/ |_/     /_/ /_____/\____/_/ /_/\n```")
			
	#help message. To be edited
	elif message.content.startswith('!help'):
		await client.send_message(message.channel, "Ranks/roles are based on your performance in the #experiment channel. The 3 people who post the most get the 'top' tole. You also get a special color for when you post an image {} days or more in a row.\n\nIn the #creative channel, every submission is worth 5 points, and every additional reaction with the 'sigma' symbol is worth 10 more points. This is not completely implemented yet".format(config['main']['top_days']))
		
	#Change 'playing' status. currently not in use.
	#elif message.content.startswith('>>Change presence'):
	#await client.change_presence(game=discord.Game(name='*GAME*'))
	
	#debug - complete top list (including removed users):
	#elif message.content.startswith('#comtop'):
	#	if verbose: print("complete top list[debug]")
	#	exp_messages = [];
	#	async for log in client.logs_from(exp_channel, limit = int(config['main']['top_limit'])):
	#		exp_messages.append(log.author.id) 
	#	exp_usr_id, exp_cts = numpy.unique(exp_messages, return_counts=True) 
	#	list = ""
	#	for k in range(len(exp_usr_id)):
	#		i = exp_cts.tolist().index(heapq.nlargest(k+1, exp_cts)[-1])
	#		exp_cts[exp_cts.tolist().index(heapq.nlargest(i, exp_cts)[-1])] = 99999
	#		if server.get_member(exp_usr_id[i]):
	#			list = list + "\n > {} - {}".format(server.get_member(exp_usr_id[i]).display_name,exp_cts[i])
	#	print(list)
		
	#debug - remove all nicknames:
	#elif message.content.startswith('#rmall'):
	#	if verbose: print("removing all nicknames[debug]")
	#	for k in server.members:  
	#		if k.display_name not server.owner.display_name:
	#			await client.change_nickname(k, None )
	
	#debug - get all relevant role IDs:
	#if verbose: print("printing all IDs[debug]")
	#elif message.content.startswith('#getid'):
	#	for k in server.roles:
	#		print (k.id, k.name)
	
	#Debug: Displays message in console (verbose required)
	#if verbose: print(str(message.author.display_name) + " in " + str(message.channel) + " - " + message.content )

tokenf = open("sigma-token.txt", "r"); tokenf.seek(0); token = tokenf.readline(); tokenf.close() #read token from TXT. Privacy reasons...
client.run(token)