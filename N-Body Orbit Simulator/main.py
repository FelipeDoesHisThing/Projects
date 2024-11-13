from manimlib import *
import numpy as np
import matplotlib.pyplot as plt
import time as t

class CelestialBody:
  bodies = [] # List contains all instances of object CelestialBody
  
  def __init__(self, mass, pos, vel, radius = 0.1, color = WHITE):
    # Initializing
    self.pos = np.array(pos, dtype='d') # Initializing initial position
    self.vel = np.array(vel, dtype='d') # Initializing initial velocity
    self.mass = mass # Storing mass
    self.radius = radius # Storing radius for animation
    self.color = color # Storin color for animation
    
    self.bodyNum = len(CelestialBody.bodies) # Setting body number in array containing all bodies

def getK(poss, vels, mass, G):
  # Initializing variables
  accs = np.zeros((len(CelestialBody.bodies),3))
  
  # Turning into numpy array
  poss = np.array(poss)
  vels = np.array(vels)
  
  # Loop through the contribution of every "other" body
  for i in range(len(CelestialBody.bodies)):
    # np.delete makes sure the contributions from other bodies are taken into account
    possCurr = np.delete(poss, i, axis = 0) # Positions of "other" bodies
    massCurr = np.delete(mass, i, axis = 0) # Mass of "other" bodies
    
    for j in range(len(CelestialBody.bodies) - 1):
      # Add contributions to the acceleration due to every "other" body
      accs[i] -= G * massCurr[j] * ((poss[i] - possCurr[j]) / np.linalg.norm(poss[i] - possCurr[j]) ** 3)
  
  return [vels, accs]
  
def RK4_step(dt, G):
  # Initializing empty arrays to store "K" values for Runge-Kutta algorithm 
  # for position and velocity independently
  KR = np.zeros((4,len(CelestialBody.bodies),3))
  KV = np.zeros((4,len(CelestialBody.bodies),3))
  
  # Initializing empty arrays to store "K" values for the current step for the Runge-Kutta algorithm
  KRcurr = np.zeros((len(CelestialBody.bodies),3))
  KVcurr = np.zeros((len(CelestialBody.bodies),3))
  
  div = np.array([1,2,2,1]) # This is the constants for each iteration of "K"
  
  # Loop four times as it is RK4 and there are 4 "K's"
  for i in range(4):
    poss = []
    vels = []
    mass = []
    
    # Find input values to calculate the respective "K"
    for body, kr, kv in zip(CelestialBody.bodies, KRcurr, KVcurr):
      poss.append(body.pos + kr * dt / div[i])
      vels.append(body.vel + kv * dt / div[i])
      mass.append(body.mass)

    KRcurr, KVcurr = getK(poss, vels, mass, G) # Get value of current "K"
    KR[i], KV[i] = KRcurr, KVcurr # Set current K for position and velocity Independently
  
  for i in range(len(CelestialBody.bodies)):
    CelestialBody.bodies[i].pos += (1/6) * div @ KR[:,i] * dt # Add step
    CelestialBody.bodies[i].vel += (1/6) * div @ KV[:,i] * dt # Add step

def solve_RK4(time, dt, G=1):
  """Get positions of bodies over a given time interval using RK4 algorithm
  
  Inputs: 
    time: Time interval to simulate over    
    dt: Time step
    G: Gravitational constant, default = 1
  
  Outputs:
    positions: Position of bodies at times t * dt of format
    [[[x1,y1,z1], t],
     [[x2,y2,z2], t],
     ...
     [[xN,yN,zN], t]]
    
  """
  # Initialize empty array for position over time
  positions = np.zeros((len(CelestialBody.bodies), 3, int(time/dt)))
  
  for t in range(int(time/dt)):
    currPos = [] # Current position
    
    for body in CelestialBody.bodies:
      currPos.append(body.pos) # Append current position to index of body

    positions[:,:,t] = np.array(currPos) # Set position at time t of each body
    
    RK4_step(dt, G) # Take a RK step
  
  return np.array(positions) 
    
def fig8():
  pos1 = np.array([0.97000436, -0.24308753, 0]) / scale
  pos2 = np.array([-0.97000436, 0.24308753, 0]) / scale
  pos3 = np.array([0, 0, 0]) / scale

  vel1 = np.array([0.93240737/2, 0.8643146/2, 0]) * scale
  vel2 = np.array([0.93240737/2, 0.8643146/2, 0]) * scale
  vel3 = np.array([-0.93240737, -0.8643146,0]) * scale
  
  M = np.array([1,1,1]) * scale
  
  pos = [pos1,pos2,pos3]
  vel = [vel1,vel2,vel3]
  
  col = [WHITE, BLUE, RED]
  
  rad = [0.01,0.01,0.01]
  
  return pos, vel, M, col, rad

def figWeird():
  G = 1
  
  r = 25
  
  v = np.array([0.3471128135672417, 0.532726851767674, 0])
  
  pos1 = np.array([1, 0, 0])
  pos2 = np.array([-1, 0, 0])
  pos3 = np.array([0, 0, 0])
  
  pos4 = np.array([1, 0, 0]) + np.array([1,0,0]) * r
  pos5 = np.array([-1, 0, 0]) + np.array([1,0,0]) * r
  pos6 = np.array([0, 0, 0]) + np.array([1,0,0]) * r
  
  pos7 = np.array([1, 0, 0]) - np.array([1,0,0]) * r
  pos8 = np.array([-1, 0, 0]) - np.array([1,0,0]) * r
  pos9 = np.array([0, 0, 0]) - np.array([1,0,0]) * r
  
  pos10 = np.array([1, 0, 0]) + np.array([0,1,0]) * r
  pos11 = np.array([-1, 0, 0]) + np.array([0,1,0]) * r
  pos12 = np.array([0, 0, 0]) + np.array([0,1,0]) * r
  
  pos13 = np.array([1, 0, 0]) + np.array([0,-1,0]) * r
  pos14 = np.array([-1, 0, 0]) + np.array([0,-1,0]) * r
  pos15 = np.array([0, 0, 0]) + np.array([0,-1,0]) * r

  vel1 = v
  vel2 = v
  vel3 = -2 * v
  
  v2 = np.sqrt(G * 3  / r) 
    
  vel4 = v + v2 * np.array([0,1,0]) 
  vel5 = v + v2 * np.array([0,1,0]) 
  vel6 = -2 * v + v2 * np.array([0,1,0]) 
  
  vel7 = v - v2 * np.array([0,1,0]) 
  vel8 = v - v2 * np.array([0,1,0]) 
  vel9 = -2 * v - v2 * np.array([0,1,0]) 
  
  vel10 = v + v2 * np.array([-1,0,0]) 
  vel11 = v + v2 * np.array([-1,0,0]) 
  vel12 = -2 * v + v2 * np.array([-1,0,0]) 
  
  vel13 = v + v2 * np.array([1,0,0]) 
  vel14 = v + v2 * np.array([1,0,0]) 
  vel15 = -2 * v + v2 * np.array([1,0,0]) 
  
  M = np.array([1,1,1,1,1,1,1,1,1,1,1,1,1,1,1])
  
  pos = [pos1,pos2,pos3,pos4,pos5,pos6,pos7,pos8,pos9, pos10, pos11, pos12, pos13, pos14, pos15]
  vel = [vel1,vel2,vel3,vel4,vel5,vel6,vel7,vel8,vel9, vel10, vel11, vel12, vel13, vel14, vel15]
  col = [WHITE, BLUE, RED] * 5
  
  rad = [0.05/2, 0.05/2, 0.05/2] * 5
  
  # M = np.array([1,1,1])
  
  # pos = [pos1,pos2,pos3]
  # vel = [vel1,vel2,vel3]
  # col = [WHITE, BLUE, RED]
  
  # rad = [0.05/2, 0.05/2, 0.05/2]
  
  return pos, vel, M, col, rad, G

def figCube():
  # G = 4 * np.pi**2
  G = 1
  r = np.array([0, -0.69548, 0.69548])
  v = np.array([0.87546, -0.31950, -0.31950])
  
  pos1 = [r[0], r[1], r[2]]
  pos2 = [r[0], -r[1], -r[2]]
  pos3 = [-r[0], r[1], -r[2]]
  pos4 = [-r[0], -r[1], r[2]]

  vel1 = [v[0], v[1], v[2]]
  vel2 = [v[0], -v[1], -v[2]]
  vel3 = [-v[0], v[1], -v[2]]
  vel4 = [-v[0], -v[1], v[2]]

  pos = [pos1, pos2, pos3, pos4]
  vel = [vel1, vel2, vel3, vel4]
  M = np.array([1,1,1,1])
  col = [RED, BLUE, GREEN, ORANGE]
  rad = [0.01] * 4
  
  return pos, vel, M, col, rad, G

def solarSystem():
  ## Initializing Initial Conditions
  G = 4 * np.pi**2 
  
  # Sun
  pos0 = np.array([0, 0, 0]) 
  vel0 = np.array([0, 0, 0])
  M0 = 1
  
  # Mercury
  pos1 = np.array([0.3877005348 , 0, 0]) # In AU
  v = np.sqrt(G * M0 / 0.3877005348)
  vel1 = np.array([0, v , 0]) # in AU/year
  M1 = 1.652e-7 # In solar masses
  
  # Venus
  pos2 = np.array([0.7279411765 , 0, 0]) # In AU
  v = np.sqrt(G * M0 / 0.7279411765)
  vel2 = np.array([0, v , 0]) # in AU/year
  M2 = 2.447e-6 # In solar masses
  
  # Earth
  pos3 = np.array([1 , 0, 0]) # In AU
  # vel3 = np.array([0, 6.27777651918 , 0]) # in AU/year
  vel3 = np.array([0,2*np.pi,0])
  M3 = 0.000003 # In solar masses
  
  # Moon
  pos3_m = pos3 + np.array([0.002653 , 0, 0])
  vel3_m = vel3 + np.array([0, 0.21544285256 , 0])
  M3_m = 3.69396868e-8
  
  # Lunar Gateway
  gtWyDist = 0.0004679211/4
  v = np.sqrt(G * M3_m / gtWyDist)
  pos3_lg = pos3_m + gtWyDist * np.array([1,0,0])
  vel3_lg = vel3_m + v * np.array([0,1,0])
  M3_lg = 2.11e-25
  
  # Mars
  pos4 = np.array([1.524064171 , 0, 0]) # In AU
  v = np.sqrt(G * M0 / pos4[0])
  vel4 = np.array([0, v , 0]) # in AU/year
  M4 = 3.213e-7 # In solar masses
  
  # Jupiter
  pos5 = np.array([5.063770053 , 0, 0]) # In AU
  v = np.sqrt(G * M0 / pos5[0])
  vel5 = np.array([0, v , 0]) # in AU/year
  M5 = 9.543e-4 # In solar masses

  # Saturn
  pos6 = np.array([9.639037433 , 0, 0]) # In AU
  v = np.sqrt(G * M0 / pos6[0])
  vel6 = np.array([0, v , 0]) # in AU/year
  M6 = 2.857e-4 # In solar masses
  
  # Uranus
  pos7 = np.array([19.1909893 , 0, 0]) # In AU
  v = np.sqrt(G * M0 / pos7[0])
  vel7 = np.array([0, v , 0]) # in AU/year
  M7 = 4.365e-5 # In solar masses
  
  # Neptune
  pos8 = np.array([29.88970588 , 0, 0]) # In AU
  v = np.sqrt(G * M0 / pos8[0])
  vel8 = np.array([0, v , 0]) # in AU/year
  M8 = 5.149e-5 # In solar masses
  
  # Adding all to arrays
  pos = [pos0, pos1, pos2, pos3, pos4, pos5, pos6, pos7, pos8]
  vel = [vel0, vel1, vel2, vel3, vel4, vel5, vel6, vel7, vel8]
  M = [M0,M1,M2,M3,M4,M5,M6,M7,M8]
  col = [YELLOW, GREY, ORANGE, BLUE, RED, DARK_BROWN, LIGHT_BROWN, BLUE_B, BLUE_E]
  rad = np.array([0.05, 0.001, 0.001, 0.001, 0.0001, 0.001, 0.001, 0.001, 0.001, 0.001]) / 4
  
  return [pos,vel,M,col,rad,G]

def Error():
  G = 4 * np.pi**2 
  
  # Sun
  pos0 = np.array([0, 0, 0]) 
  vel0 = np.array([0, 0, 0])
  M0 = 1

  # Earth
  pos1 = np.array([1 , 0, 0]) # In AU
  vel1 = np.array([0, 2 * np.pi , 0]) # in AU/year
  M1 = 0.000003 # In solar masses
  
  # Moon
  pos2 = pos1 + np.array([0.002653 , 0, 0])
  v = np.sqrt(G*M1/0.002653)
  # vel2 = vel1 + np.array([0, 0.21544285256 , 0])
  vel2 = vel1 + np.array([0, v, 0])
  M2 = 3.69396868e-8

  pos = [pos0, pos1]
  vel = [vel0, vel1]
  M = [M0, M1]
  col = [YELLOW, BLUE]
  rad = np.array([0.05, 0.001]) / 4
  
  return [pos,vel,M,col,rad,G]

sim_time = 500
# run_time = sim_time/100
run_time = 10
dt = 0.001 # Time Step

class NBodyProblem(Scene):
  def construct(self):
    pos, vel, M, col = figCube()
    # pos, vel, M, col = figWeird()
    # pos, vel, M, col = solarSystem()
  
    # Initializing bodies in scene with initial conditions
    for i in range(len(M)):
      CelestialBody.bodies.append(CelestialBody(M[i], pos[i], vel[i], color = col[i]))
      
    position = solve_RK4(time, dt)

    curves = VGroup()
    
    axes = ThreeDAxes(
      x_range=(-1,1,0.5),
      y_range=(-1,1,0.5),
      z_range=(-1,1,0.5)
    )
    
    axes.center()
    self.add(axes)
    
    for i in range(len(CelestialBody.bodies)):
      curve = VMobject().set_points_as_corners(position[i,:,:].T)
      curve.set_stroke(CelestialBody.bodies[i].color)
      curves.add(curve)
    
    dots = Group(GlowDot(color = body.color) for body in CelestialBody.bodies)
    
    def updateDots(dots, curves=curves):
      for dot, curve in zip(dots, curves):
        dot.move_to(curve.get_end())
    
    dots.add_updater(updateDots)
    
    tail = VGroup(
        TracingTail(dot, time_traced = 10).match_color(dot)
        for dot in dots
    )
    
    self.add(dots)
    self.add(tail)
    curves.set_opacity(0)
    
    frame = self.camera.frame
    
    frame.set_height(curves.get_center_of_mass()[1] + 4)
    frame.set_euler_angles(phi=60 * DEGREES)
    # frame.add_updater(lambda m, dt: m.increment_phi(-0.05 * dt))
    frame.add_updater(lambda m, dt: m.increment_theta(0.2 * dt))
    
    
    # self.play(
    #   *(ShowCreation(curve, rate_func = linear)
    #     for curve in curves), 
    #   run_time = time
    #   )

class OrbitingFig8(Scene):
  def construct(self):
    pos, vel, M, col, rad, G = figWeird()
  
    # Initializing bodies in scene with initial conditions
    for i in range(len(M)):
      CelestialBody.bodies.append(CelestialBody(M[i], pos[i], vel[i], radius = rad[i], color = col[i]))
    
    # region 
    axes = NumberPlane(x_range=(-10,10,5),
                       y_range=(-10,10,5))
    
    axes.set_color(WHITE)
    
    axes.center()
    # self.add(axes)
    
    position = solve_RK4(sim_time, dt, G)
    
    curves = VGroup()
    for i in range(len(CelestialBody.bodies)):
      curve = VMobject().set_points_as_corners(position[i].T)
      curve.set_stroke(CelestialBody.bodies[i].color)
      curves.add(curve)
    
    dots = Group(Sphere(color = body.color, radius = body.radius) for body in CelestialBody.bodies)
    
    def updateDots(dots):
      for dot, curve in zip(dots, curves):
        dot.move_to(curve.get_end())
    
    self.add(dots)
    dots.add_updater(updateDots)
    
    tail = VGroup(
        TracingTail(dot, time_traced =  run_time / 10).match_color(dot)
        for dot in dots
    )
    
    self.add(tail)
    
    frame = self.camera.frame

    frame.move_to(ORIGIN)
    frame.set_height(ORIGIN + 3)
    # frame.set_euler_angles(phi = 60 * DEGREES)

    COM = Group(Sphere(color = GREEN, radius = dots[0].radius) for systems in dots[i:i+3] for i in [0,3,6,9,12])

    def updateCOM(COM):
      for com,i in zip(COM, [0,3,6,9,12]):
        com.move_to(dots[i:i+3].get_center_of_mass())
    
    self.add(COM)
    COM.add_updater(updateCOM) 
    
    
    tail2 = VGroup(
        TracingTail(COM, time_traced = run_time/2).match_color(COM)
        for COM in COM
    )
    
    self.add(tail2)
    COM.set_opacity(0)
    
    curves.set_opacity(0)
    # endregion
    
    self.play(*(ShowCreation(curve, run_time = run_time, rate_func = linear) for curve in curves),
              frame.animate.set_height(ORIGIN + 60).set_anim_args(run_time = run_time/2, rate_func = rush_into)
              )

class Figure8(Scene):
  def construct(self):
    G = 1
    pos, vel, M, col, rad = fig8()
  
    # Initializing bodies in scene with initial conditions
    for i in range(len(M)):
      CelestialBody.bodies.append(CelestialBody(M[i], pos[i], vel[i], radius = rad[i], color = col[i]))
    

    axes = NumberPlane(x_range=(-10,10,5),
                       y_range=(-10,10,5))
    
    axes.set_color(WHITE)
    
    axes.center()
    # self.add(axes)
    
    dots = Group(Sphere(color = body.color, radius = body.radius) for body in CelestialBody.bodies)
    
    def updateDots(dots):
      for dot, body in zip(dots, CelestialBody.bodies):
        dot.move_to(body.pos)
    
    self.add(dots)
    dots.add_updater(updateDots)
    
    tail = VGroup(
        TracingTail(dot, time_traced = scale/2).match_color(dot)
        for dot in dots
    )
    
    self.add(tail)
    
    frame = self.camera.frame
    frame.move_to(dots.get_center_of_mass())
    frame.set_height(ORIGIN + 2)
    # frame.set_euler_angles(phi = 60 * DEGREES)
    
    start_time = t.time()   
    while 1:
      self.play(ShowCreation(dots), run_time=0.000001)
      RK4_step(dt, G)

class FigureCube(Scene):
  def construct(self):
    # G = 1
    pos, vel, M, col, rad, G = figCube()
  
    # Initializing bodies in scene with initial conditions
    for i in range(len(M)):
      CelestialBody.bodies.append(CelestialBody(M[i], pos[i], vel[i], radius = rad[i], color = col[i]))
    

    axes = ThreeDAxes(x_range=(-1,1,0.5),
                       y_range=(-1,1,0.5),
                       z_range=(-1,1,0.5))
    
    axes.set_color(WHITE)
    
    axes.center()
    # self.add(axes)
    
    position1 = solve_RK4(sim_time, dt, G)
    
    curves = VGroup()
    for i in range(len(CelestialBody.bodies)):
      curve = VMobject().set_points_as_corners(position1[i].T)
      curve.set_stroke(CelestialBody.bodies[i].color)
      curves.add(curve)
    
    dots = Group(Sphere(color = body.color, radius = body.radius) for body in CelestialBody.bodies)
    
    def updateDots(dots):
      for dot, curve in zip(dots, curves):
        dot.move_to(curve.get_end())
    

    tail = VGroup(
        TracingTail(dot, time_traced = run_time/4).match_color(dot)
        for dot in dots
    )

    frame = self.camera.frame
    frame.move_to(dots.get_center_of_mass()).set_height(ORIGIN + 3).set_euler_angles(phi=0*DEGREES)
    
    curves.set_opacity(0)
    
    
    self.add(dots)
    dots.add_updater(updateDots)
    self.add(tail)
    
    self.play(*(ShowCreation(curve) for curve in curves), 
              # frame.animate.set_height(ORIGIN + 10),
              run_time = run_time, rate_func = linear)

class SolarSystemSun(Scene):
  def construct(self):
    
    pos, vel, M, col, rad, G = solarSystem()
  
    # Initializing bodies in scene with initial conditions
    for i in range(len(M)):
      CelestialBody.bodies.append(CelestialBody(M[i], pos[i], vel[i], radius = rad[i], color = col[i]))
    
    position = solve_RK4(sim_time, dt, G)

    with open('solarSystem.npy', 'wb') as f:
      np.save(f, position)
    
    # region Animation stuff
    curves = VGroup()
    for i in range(len(CelestialBody.bodies)):
      curve = VMobject().set_points_as_corners(position[i].T)
      curve.set_stroke(CelestialBody.bodies[i].color)
      curves.add(curve)
    
    dots = Group(GlowDot(color = body.color, radius = body.radius) for body in CelestialBody.bodies)
    
    tail = VGroup(
        TracingTail(dot, time_traced=run_time/5).match_color(dot)
        for dot in dots)

    curves.set_opacity(0)
    
    frame = self.camera.frame
    
    def updateDots(dots):
      for dot, curve in zip(dots, curves):
        dot.move_to(curve.get_end())

    frame.set_height(dots[0].get_center() + 2)
    frame.set_euler_angles(phi = 60 * DEGREES)
    dots.add_updater(updateDots)    
    # endregion
    
    self.play(FadeIn(dots))
    self.add(tail)
    self.play(*(ShowCreation(curve, rate_func = linear, run_time = run_time) for curve in curves),
              frame.animate.set_height(dots[0].get_center() + 40).set_anim_args(run_time = run_time, rate_func = there_and_back))
    self.play(*[FadeOut(mob) for mob in self.mobjects])
   
class SolarSystemEarth(Scene):
  def construct(self):
    
    pos, vel, M, col, rad, G = solarSystem()
  
    # Initializing bodies in scene with initial conditions
    for i in range(len(M)):
      CelestialBody.bodies.append(CelestialBody(M[i], pos[i], vel[i], radius = rad[i], color = col[i]))
    
    position = solve_RK4(sim_time, dt, G)
 
    # region Animation stuff
    curves = VGroup()
    for i in range(len(CelestialBody.bodies)):
      curve = VMobject().set_points_as_corners(position[i].T)
      curve.set_stroke(CelestialBody.bodies[i].color)
      curves.add(curve)
    
    dots = Group(GlowDot(color = body.color, radius = body.radius) for body in CelestialBody.bodies)
    
    tail = VGroup(
        TracingTail(dot, time_traced=run_time/10).match_color(dot)
        for dot in dots)

    curves.set_opacity(0)
    
    frame = self.camera.frame
    
    def updateDots(dots):
      for dot, curve in zip(dots, curves):
        dot.move_to(curve.get_end())
    
    def updateCam(frame):
      frame.move_to(curves[3].get_end())

    
    # frame.set_height(dots[1].get_center() + 0.01)
    # frame.set_euler_angles(phi = 75 * DEGREES)
    
    frame.set_height(dots[3].get_center() + 0.01)
    frame.set_euler_angles(phi = 75 * DEGREES)
    dots.add_updater(updateDots)
    frame.add_updater(updateCam)
    
    # endregion
    
    self.play(FadeIn(dots))
    self.add(tail)
    self.play(*(ShowCreation(curve, rate_func = linear, run_time = run_time) for curve in curves))
    self.play(*[FadeOut(mob) for mob in self.mobjects])
      
class SolarSystemMoon(Scene):
  def construct(self):
    
    pos, vel, M, col, rad, G = solarSystem()
  
    # Initializing bodies in scene with initial conditions
    for i in range(len(M)):
      CelestialBody.bodies.append(CelestialBody(M[i], pos[i], vel[i], radius = rad[i], color = col[i]))
    
    position = solve_RK4(sim_time, dt, G)
 
    # region Animation stuff
    curves = VGroup()
    for i in range(len(CelestialBody.bodies)):
      curve = VMobject().set_points_as_corners(position[i].T)
      curve.set_stroke(CelestialBody.bodies[i].color)
      curves.add(curve)
    
    dots = Group(GlowDot(color = body.color, radius = body.radius) for body in CelestialBody.bodies)
    
    tail = VGroup(
        TracingTail(dot, time_traced=run_time/10).match_color(dot)
        for dot in dots)

    curves.set_opacity(0)
    
    frame = self.camera.frame
    
    def updateDots(dots):
      for dot, curve in zip(dots, curves):
        dot.move_to(curve.get_end())
    
    def updateCam(frame):
      frame.move_to(curves[4].get_end())

 
    frame.set_height(dots[4].get_center() + 0.0005)
    frame.set_euler_angles(phi = 85 * DEGREES)
    dots.add_updater(updateDots)
    frame.add_updater(updateCam)
    
    # endregion
    
    self.play(FadeIn(dots))
    self.add(tail)
    self.play(*(ShowCreation(curve, rate_func = linear, run_time = run_time) for curve in curves))
    self.play(*[FadeOut(mob) for mob in self.mobjects])

class ErrorTest(Scene):
  def construct(self):
    pos, vel, M, col, rad, G = Error()
  
    # Initializing bodies in scene with initial conditions
    for i in range(len(M)):
      CelestialBody.bodies.append(CelestialBody(M[i], pos[i], vel[i], radius = rad[i], color = col[i]))
    
    positionNumerical = solve_RK4(sim_time, dt, G)
  
  
    # region Animation stuff
    curves = VGroup()
    for i in range(len(CelestialBody.bodies)):
      curve = VMobject().set_points_as_corners(positionNumerical[i].T)
      curve.set_stroke(CelestialBody.bodies[i].color)
      curves.add(curve)
        
    dots = Group(GlowDot(color = body.color, radius = body.radius) for body in CelestialBody.bodies)
    
    tail = VGroup(
        TracingTail(dot, time_traced=run_time/2).match_color(dot)
        for dot in dots)

    curves.set_opacity(0)
    
    frame = self.camera.frame
    
    def updateDots(dots):
      for dot, curve in zip(dots, curves):
        dot.move_to(curve.get_end())
    
    def updateCam(frame):
      frame.move_to(curves[0].get_end())


    # frame.set_height(dots[0].get_center() + 5)
    # frame.set_euler_angles(phi = 85 * DEGREES)
    dots.add_updater(updateDots)
    # frame.add_updater(updateCam)
    
    # endregion
    
    
    self.play(FadeIn(dots))
    self.add(tail)
    self.play(*(ShowCreation(curve, rate_func = linear, run_time = run_time) for curve in curves))
    self.play(*[FadeOut(mob) for mob in self.mobjects])


def main():
  # Figure8().construct()
  # FigureCube().construct()
  # OrbitingFig8().construct()
  
  SolarSystemSun().construct() # 100 Years
  # SolarSystemEarth().construct() # 5 Years
  # SolarSystemMoon().construct() # 1 Year
  
  # # ErrorTest().construct()
  # pos, vel, M, col, rad, G = Error()
  
  #   # Initializing bodies in scene with initial conditions
  # for i in range(len(M)):
  #   CelestialBody.bodies.append(CelestialBody(M[i], pos[i], vel[i], radius = rad[i], color = col[i]))
    
  # position = solve_RK4(sim_time, dt, G)

  # with open('SunEarthMoonSystem.npy', 'wb') as f:
  #   np.save(f, position)
  
  # with open('SunEarthMoonSystem.npy', 'rb') as f:
  #   position = np.load(f)
  
  # t = np.arange(0, sim_time,dt)
  
  # # for i in range(8):
  # #   plt.plot(t, np.linalg.norm(position[i+1], axis=0))
  
  # # plt.plot(t, np.abs(np.linalg.norm(position[1],axis=0)))
  
  # # Finding best fit for error
  # end = max(np.abs(np.linalg.norm(position[1],axis=0)-1))
  # time = np.where(np.abs(np.linalg.norm(position[1],axis=0)-1)==end)[0] * dt
  # multiplier = end/time
  # error = np.array([np.cos(2*np.pi*t),np.sin(2*np.pi*t)]) * (multiplier * t)
  
  # plt.plot(t, np.abs(np.linalg.norm(position[1],axis=0)-1), linewidth=1)
  # plt.plot(t, np.abs(error[1]))
  # # plt.plot(t,)
  # plt.show()

if __name__ == "__main__":
  main()
  
  
