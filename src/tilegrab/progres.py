import sys
import time


class ProgressBar:
	'''
	Progress bar
	'''

	p_bar_width = 50

	def init_progress(self, prefix, total):

		self.pbar_prefix  = prefix
		self.pbar_counter = 0
		self.pbar_total   = total
		self.start_time   = time.time()

	def progress(self):

		self.pbar_counter += 1

		try:
			x = int(self.pbar_counter/self.pbar_total*self.p_bar_width)
		except Exception as e:
			x = 1

		elapsed = time.time() - self.start_time

		mins, sec = divmod(elapsed, 60)
		time_str = f"{int(mins):02}:{int(sec):02}"

		pbar_text = f"{self.pbar_prefix} [{u'■'*x}{('·'*(self.p_bar_width-x))}] {self.pbar_counter} of {self.pbar_total} {int(self.pbar_counter/self.pbar_total*100)}% {time_str}"

		print(pbar_text, end='\r', file=sys.stdout, flush=True)

	@property
	def pbar_count(self):
		return self.pbar_counter

	@pbar_count.setter
	def pbar_count(self, count):
		self.pbar_counter = count
