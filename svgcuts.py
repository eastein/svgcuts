import random
import copy
import math

SVG_BASE='<!DOCTYPE svg PUBLIC "-//W3C//DTD SVG 1.0//EN" "http://www.w3.org/TR/2001/REC-SVG-20010904/DTD/svg10.dtd"><svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="%f%s" height="%f%s">%s</svg>'
#LINE="<polyline points='%f%s %f%s, %f%s %f%s' stroke-width='0.1' stroke='black' style='fill: none;' />"
LINE="<line x1='%f%s' y1='%f%s' x2='%f%s' y2='%f%s' stroke-width='1' stroke='%s' style='fill: none;' />"
UNIT = "px"

class Transformable(object) :
	"""
	"""
	pass

class Point(object) :
	def __init__(self, x, y) :
		self.x = x
		self.y = y

	def __eq__(self, other) :
		return self.x == other.x and self.y == other.y

	def __repr__(self) :
		return 'Point<%f,%f>' % (self.x, self.y)

	def __str__(self) :
		return repr(self)

	def __cmp__(self, other) :
		return repr(self).__cmp__(repr(other))

	def distance(self, p2) :
		return math.pow(math.pow(float(self.x) - float(p2.x), 2) + math.pow(float(self.y) - float(p2.y), 2), 0.5)

	def translate(self, x, y) :
		self.x += x
		self.y += y

	def scale(self, xm, ym) :
		self.x *= xm
		self.y *= ym

class Line(object) :
	def __init__(self, p1, p2, unit='px', color="black") :
		self.p1 = p1
		self.p2 = p2
		self.unit = unit
		self.color = color
	
	def __repr__(self) :
		return 'Line<%s,%s>' % (self.p1, self.p2)

	def __str__(self) :
		return repr(self)

	@property
	def length(self) :
		return self.p1.distance(self.p2)

	@property
	def reverse(self) :
		return Line(self.p2, self.p1)

	"""
	@throws ZeroDivisionError if slope is infinite
	"""
	@property
	def slope_offset(self) :
		slope = (float(self.p2.y) - self.p1.y) / (float(self.p2.x) - self.p1.x)
		return slope, self.p1.y - (self.p1.x * slope)

	def x_falls_within(self, x) :
		if self.p1.x <= self.p2.x :
			return (self.p1.x <= x) and (self.p2.x >= x)
		else :
			return (self.p2.x <= x) and (self.p1.x >= x)

	def y_falls_within(self, y) :
		if self.p1.y <= self.p2.y :
			return (self.p1.y <= y) and (self.p2.y >= y)
		else :
			return (self.p2.y <= y) and (self.p1.y >= y)

	@property
	def angle(self) :
		try :
			angle = math.atan(self.slope_offset[0])
		except ZeroDivisionError :
			# -90 degrees exists!
			if self.p2.y > self.p1.y :
				angle = math.pi / 2.0
			elif self.p1.y > self.p2.y :
				angle = math.pi / -2.0
			else :
				print 'about to have a terminal error determining angle of line %s' % self
				raise

		if self.p2.x < self.p1.x :
			if angle + math.pi < math.pi :
				return angle + math.pi
			else :
				return angle - math.pi
		else :
			return angle

	def incident_angle(self, l2) :
		incident = abs(l2.angle - self.angle)
		#print '!!! computed incident_angle before any munging to be %fpi' % (incident / math.pi)
		if incident >= math.pi :
			incident = 2.0 * math.pi - incident

		assert incident >= 0

		if self.shared_points(l2) > 0 :
			# shared points; flip obtuse/acute if the "start ends" aren't the same.
			if self.p1 == l2.p2 or self.p2 == l2.p1 :
				incident = math.pi - incident
		else :
			# TODO perhaps try to determine how much of the "short end" of the intersected line is cut off and call it a non-
			# intersection if so?
			# no shared points; we must use intersection as our guide.
			if self.intersects(l2, onlines=1) :
				# intersects; in this case, we want to make all obtuse angles acute
				if incident > math.pi / 2.0 :
					return math.pi - incident
			else :
				# no intersects; in this case, we want to make all acute angles obtuse
				if incident < math.pi / 2.0 :
					return math.pi - incident

		return incident

	def closest_distance(self, l2) :
		distance =               self.p1.distance(l2.p1)
		distance = min(distance, self.p1.distance(l2.p2))
		distance = min(distance, self.p2.distance(l2.p1))
		distance = min(distance, self.p2.distance(l2.p2))

		#print 'point to point distance: %f' % distance

		# this function's code is not valid if it is possible for the closest approach of 2 straight line segments to not be at either end of either line

		"""
		For a line, if the angle beween the line and the line created by using the first point in the line and the point given is acute
		and the same if you use the other end of the line segment (the closest point between the point and the line is not at one 
		of the line endpoints), return the closest known distance (or the given already known closest known distance if it's closer)
		"""
		def evaluate_distance_point_to_line_middle(distance, line, point) :
			# if we're not going anywhere, we know that already and this is a waste of time.
			if line.p1 == point :
				return distance

			reach_line = Line(line.p1, point)
			reach_angle = line.incident_angle(reach_line)

			#print '    angle from %s to %s is %fpi' % (line, reach_line, reach_angle / math.pi)

			# must be acute
			if reach_angle > math.pi / 2 :
				#print 'reach angle is %f, aborting due to obtusity' % reach_angle
				return distance

			reach_length = reach_line.length
			line_length = line.length
			#print 'reach %f, line %f' % (reach_length, line_length)
			
			if math.cos(reach_angle) * reach_length < line_length  :
				#print 'hypotenuse for computation is %f' % reach_length
				distance_this = math.sin(reach_angle) * reach_length
				#print 'determined that the distance is %f from %s to %s' % (distance_this, line, point)
				return min(distance, distance_this)

			#print 'returning default, couldnt find a short distance'
			return distance

		distance = evaluate_distance_point_to_line_middle(distance, self, l2.p1)
		distance = evaluate_distance_point_to_line_middle(distance, self.reverse, l2.p1)
		#print 'edp1 %f' % distance
		distance = evaluate_distance_point_to_line_middle(distance, self, l2.p2)
		distance = evaluate_distance_point_to_line_middle(distance, self.reverse, l2.p2)
		#print 'edp2 %f' % distance
		distance = evaluate_distance_point_to_line_middle(distance, l2, self.p1)
		distance = evaluate_distance_point_to_line_middle(distance, l2.reverse, self.p1)
		#print 'edp3 %f' % distance
		distance = evaluate_distance_point_to_line_middle(distance, l2, self.p2)
		distance = evaluate_distance_point_to_line_middle(distance, l2.reverse, self.p2)
		#print 'edp4 %f' % distance

		return distance

	# TODO make this use __cmp__ or __eq__ somehow, set() is acting odd
	def shared_points(self, l2) :
		self_points = set([str(self.p1), str(self.p2)])
		l2_points = set([str(l2.p1), str(l2.p2)])
		
		n = len(self_points.intersection(l2_points))
		return n
	
	def intersects(self, l2, onlines=2) :
		vert1 = False
		vert2 = False
		try :
			a1, b1 = self.slope_offset
		except ZeroDivisionError :
			vert1 = True
		try :
			a2, b2 = l2.slope_offset
		except ZeroDivisionError :
			vert2 = True

		if vert1 and vert2 :
			# the only way is if they are at the same x position exactly and the endpoints of y fall within the first line
			return self.p1.x == l2.p1.x and (self.y_falls_within(l2.p1.y) or self.y_falls_within(l2.p2.y))
		elif vert1 :
			# FIXME check for onlines, more thorough testing
			# the y coordinate where the intersection occurs
			y2 = self.p1.x * a2 + b2
			return self.y_falls_within(y2) and l2.x_falls_within(self.p1.x)
		elif vert2 :
			# FIXME check for onlines, more thorough testing
			# the y coordinate where the intersection occurs
			y2 = l2.p1.x * a1 + b1
			return l2.y_falls_within(y2) and self.x_falls_within(l2.p1.x)
		else :
			if a1 == a2 :
				# slopes are equal; they only intersect if the their offsets are also equal and 
				# the x dimensions overlap
				if b1 != b2 :
					return False

				return self.x_falls_within(l2.p1.x) or self.x_falls_within(l2.p2.x)

			# slopes are non equal.... find the x and y solutions of the set of equations
			x = (float(b2) - b1) / (float(a1) - a2)
			y = a2 * x + b2

			onlines_counted = 0
			if self.x_falls_within(x) and self.y_falls_within(y) :
				onlines_counted += 1
			if l2.x_falls_within(x) and l2.y_falls_within(y) :
				onlines_counted += 1
			return onlines_counted >= onlines

	@property
	def svg(self) :
		return LINE % (self.p1.x, self.unit,  self.p1.y, self.unit,  self.p2.x, self.unit,  self.p2.y, self.unit, self.color)

class Layer(object) :
	def __init__(self, xw, yw, unit="px") :
		self.xw = xw
		self.yw = yw
		self.lines = list()
		self.texts = list()
		self.circles = list()
		self.also_cut = list()
		self.unit = unit

	def add_line(self, line) :
		line.unit = self.unit
		self.lines.append(line)
		for cuts in self.also_cut :
			cuts.add_line(line)

	def add_text(self, x, y, text, fontfam='Helvetica', fontsize=10) :
		self.texts.append((x,y,text,fontfam,fontsize))
		for cuts in self.also_cut :
			cuts.add_text(x, y, text, fontfam=fontfam, fontsize=fontsize)

	def add_circle(self, x, y, radius) :
		self.circles.append((x,y,radius))
		for cuts in self.also_cut :
			cuts.add_circle(x, y, radius)

	def assert_n_intersections(self, maxn=None) :
		n = 0
		nlines = len(self.lines)
		for i in xrange(nlines) :
			for j in xrange(i+1, nlines) :
				l1 = self.lines[i]
				l2 = self.lines[j]
				if l1.intersects(l2) and not l1.shared_points(l2) :
					n += 1
					if maxn is not None and n > maxn :
						return False

		return n

	def assert_n_close_acutes(self, theta, dist, maxn=None) :
		n = 0
		nlines = len(self.lines)
		for i in xrange(nlines) :
			for j in xrange(i+1, nlines) :
				l1 = self.lines[i]
				l2 = self.lines[j]
				if l1.closest_distance(l2) <= dist and l1.incident_angle(l2) <= theta :
					n += 1
					if maxn is not None and n > maxn :
						return False
		return n

	#### knapsack ####

	def copy_from(self, l, xtr, ytr) :
		#print 'copying with translates', xtr, ytr
		lines = copy.deepcopy(l.lines)
		for l in lines :
			# XXX figure out why i'm having to divide this by 2, WORKAROUND LOL
			l.p1.x += xtr / 2.0
			l.p2.x += xtr / 2.0
			l.p1.y += ytr / 2.0
			l.p2.y += ytr / 2.0
			self.add_line(l)

	def pack(self, layers) :
		"""
		@param layers List of tuples. Each tuple is (layer, count) for how many should be included.

		This function packs the objects into the layer, if possible. Rectangular bounding boxes are used.

		This should be done mostly optimally. If we're packing something in, it should to be done as efficiently as possible. If a space available matches very closely to the size of a layer to be packed, then do that.
		"""
		class AvailNode(object) :
			def __cmp__(self, oan) :
				return cmp(self.area(), oan.area())

			def area(self) :
				return self.xsz * self.ysz

			class NoFit(Exception) :
				pass

			# how far apart things have to be
			PAD = .025
			# how much area a note during guillotine can get before it's not suballocated
			# if the piece that just got placed is smaller than this, the area (with padding)
			# of the piece that just got placed is treated as the toss area
			TOSS_A = 0.0125
			def __init__(self, on_layer, xpos, ypos, xsz, ysz) :
				self.on_layer = on_layer
				self.xpos = xpos
				self.ypos = ypos
				self.xsz = xsz
				self.ysz = ysz

				#print 'creating new node at %f %f' % (self.xpos, self.ypos)

				DEBUG = False

				if DEBUG :
					unit = on_layer.unit
					in_pad = .01
					pts = [
						Point(self.xpos + in_pad, self.ypos + in_pad),
						Point(self.xpos + self.xsz - in_pad, self.ypos + in_pad),
						Point(self.xpos + self.xsz - in_pad, self.ypos + self.ysz - in_pad),
						Point(self.xpos + in_pad, self.ypos + self.ysz - in_pad),
					]
					for i in range(len(pts)) :
						p1 = pts[i]
						p2 = pts[(i + 1) % len(pts)]
						on_layer.add_line(Line(p1, p2, unit=unit))
			
			def sub(self, xpos, ypos, xsz, ysz) :
				return self.__class__(self.on_layer, self.xpos + xpos, self.ypos + ypos, xsz, ysz)

			"""
			Return optimality of the fit, what ratio of the padded area of the piece will be used if
			placed here. We want to totally fill up the subsections if possible.
			this will optimize for placing large things first and using small areas first.
			"""
			def fit(self, layer) :
				xpad = (layer.xw + self.PAD * 2)
				ypad = (layer.yw + self.PAD * 2)
				apad = xpad * ypad

				this_area = self.xsz  * self.ysz
				if xpad > self.xsz :
					raise self.NoFit
				elif ypad > self.ysz :
					raise self.NoFit
				
				return apad / this_area

			def place(self, layer) :
				class CUT :
					class V :
						pass
					class H :
						pass
				CUT_OPTS = [CUT.V, CUT.H]

				# TODO make deciding to cut vertically or horizontally smarter than this
				xpad = (layer.xw + self.PAD * 2)
				ypad = (layer.yw + self.PAD * 2)
				apad = xpad * ypad

				atoss = min(apad, self.TOSS_A)

				xspare = self.xsz - xpad
				yspare = self.ysz - ypad

				possibles = dict()
				for cut in CUT_OPTS :
					p = []
					def add_option(p, cut, xp, yp, xs, ys) :
						a = xs * ys
						if a < atoss :
							return
						p.append((a, cut, xp, yp, xs, ys))

					if cut == CUT.H :
						#print ypad
						add_option(p, cut, xpad, 0.0, xspare, ypad)
						add_option(p, cut, 0.0, ypad, self.xsz, yspare)
					elif cut == CUT.V :
						add_option(p, cut, 0.0, ypad, xpad, yspare)
						add_option(p, cut, xpad, 0.0, xspare, self.ysz)

					if p :
						possibles[cut] = list(p)

				max_spares = None
				max_saved = None
				for (ct, spares) in possibles.items() :
					ta = reduce(lambda a,b: a+b, [a for (a, cut, xp, yp, xs, ys) in spares])
					if max_saved is None :
						max_spares = spares
						max_saved = ta
					elif ta > max_saved :
						max_spares = spares
						max_saved = ta

				#print 'spare subsegments are %s' % max_spares
				#print 'copying in'
				r = []
				self.on_layer.copy_from(layer, self.xpos + self.PAD, self.ypos + self.PAD)
				if max_spares :
					#print 'did cut: %s' % str(max_spares[0][1])

					for (a, cut, xp, yp, xs, ys) in max_spares :
						#print xp, yp, xs, ys
						r.append(self.sub(xp, yp, xs, ys))
				return r

		avail_nodes = [
			AvailNode(self, 0.0, 0.0, self.xw, self.yw)
		]

		unplaced = list(layers)
		
		per = [20, 30, 100, 1000, None]
		progress = True
		while unplaced and progress and avail_nodes :
			# try putting them in a random order!
			avail_nodes.sort(reverse=True)
			progress = False

			while progress is False :
				try :
					use_node = avail_nodes.pop()
				except IndexError :
					# nope, nowhere to put it!
					break

				for try_thistime in per :
					if try_thistime is None :
						# try them all, oh well
						try_thistime = len(unplaced)
					else :
						try_thistime = min(try_thistime, len(unplaced))
					best_fr = None
					best_layer = None

					random.shuffle(unplaced)

					for i in range(try_thistime) :
						trying = unplaced[i]
						try :
							fr = use_node.fit(trying)
							#print 'fr is %f' % fr
							if (best_fr is None) or (fr > best_fr) :
								best_fr = fr
								best_layer = trying
						except AvailNode.NoFit :
							continue

					if best_layer :
						unplaced.remove(best_layer)
						avail_nodes += use_node.place(best_layer)
						progress = True
						break
		return unplaced
	#### conversion to svg ####

	def render(self) :
		return SVG_BASE % (self.xw, self.unit, self.yw, self.unit, ''.join(\
			[line.svg for line in self.lines] + \
			['<text x="%f%s" y="%f%s" font-family="%s" font-size="%dpt" fill="black">%s</text>' % (x, self.unit, y, self.unit, fontfam, fontsize, text) for (x, y, text, fontfam, fontsize) in self.texts] + \
			['<circle cx="%f%s" cy="%f%s" r="%f%s" stroke="black" stroke-width="1" fill="none"/>' % (x, self.unit, y, self.unit, r, self.unit) for (x, y, r) in self.circles]))

	def write(self, fn) :
		fh = open(fn, 'w')
		try :
			fh.write(self.render())
		finally :
			fh.close()
