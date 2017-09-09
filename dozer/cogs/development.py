import copy, discord, importlib, re
from ._utils import *

class Development(Cog):
	eval_globals = {}
	for module in ('asyncio', 'collections', 'discord', 'inspect', 'itertools'):
		eval_globals[module] = __import__(module)
	eval_globals['__builtins__'] = __import__('builtins')
	
	@command()
	async def reload(self, ctx, cog):
		"""Reloads a cog."""
		extension = 'dozer.cogs.' + cog
		msg = await ctx.send('Reloading extension %s' % extension)
		self.bot.unload_extension(extension)
		self.bot.load_extension(extension)
		await msg.edit(content='Reloaded extension %s' % extension)
	
	@command(name='eval')
	async def evaluate(self, ctx, *, code):
		"""Evaluates Python. Await is valid and `{ctx}` is the command context."""
		if code.startswith('```'): code = code.strip('```').partition('\n')[2].strip() # Remove multiline code blocks
		else: code = code.strip('`').strip() # Remove single-line code blocks, if necessary
		
		e = discord.Embed(type='rich')
		e.add_field(name='Code', value='```py\n%s\n```' % code, inline=False)
		try:
			locals_ = locals()
			load_function(code, self.eval_globals, locals_)
			ret = await locals_['evaluated_function'](ctx)
			
			e.title = 'Python Evaluation - Success'
			e.color = 0x00FF00
			e.add_field(name='Output', value='```\n%s (%s)\n```' % (repr(ret), type(ret)), inline=False)
		except Exception as err:
			e.title = 'Python Evaluation - Error'
			e.color = 0xFF0000
			e.add_field(name='Error', value='```\n%s\n```' % repr(err))
		await ctx.send(embed=e)
	
	@command(name='su', pass_context=True)
	async def pseudo(self, ctx, user : discord.Member, *, command):
		"""Execute a command as another user."""
		msg = copy.copy(ctx.message)
		msg.author = user
		msg.content = command
		context = await self.bot.get_context(msg)
		return await self.bot.invoke(context)

def load_function(code, globals_, locals_):
	function_header = 'async def evaluated_function(ctx):'
	
	lines = code.splitlines()
	if len(lines) > 1:
		indent = 4
		for line in lines:
			line_indent = re.search(r'\S', line).start() # First non-WS character is length of indent
			if line_indent:
				indent = line_indent
				break
		line_sep = '\n' + ' ' * indent
		exec(function_header + line_sep + line_sep.join(lines), globals_, locals_)
	else:
		try:
			exec(function_header + '\n\treturn ' + lines[0], globals_, locals_)
		except SyntaxError as err: # Either adding the 'return' caused an error, or it's user error
			if err.text[err.offset-1] == '=' or err.text[err.offset-3:err.offset] == 'del' or err.text[err.offset-6:err.offset] == 'return': # return-caused error
				exec(function_header + '\n\t' + lines[0], globals_, locals_)
			else: # user error
				raise err

def setup(bot):
	bot.add_cog(Development(bot))