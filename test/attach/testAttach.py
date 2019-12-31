import unittest
from pygdbmi import gdbcontroller
import os

LLDBMI_PATH = 'lldb-mi'
TESTDATA = os.path.join( os.path.dirname( __file__ ), '..', 'testdata' )
SIMPLE = os.path.join( TESTDATA, 'simple' )


gdbcontroller.DEFAULT_GDB_TIMEOUT_SEC = 2


class TestLLDBMIAttach( unittest.TestCase ):
  def test_BreakOnMain( self ):
    controller = gdbcontroller.GdbController(
      gdb_path = LLDBMI_PATH,
      gdb_args = [ '--interpreter=mi' ],
      verbose = True )

    input( f"GDB PID is {controller.gdb_process.pid}..." )

    try:
      controller.write( f'-gdb-set auto-solib-add on' )
      controller.write( f'-gdb-set solib-search-path "{SIMPLE}"' )
      controller.write( f'-environment-cd {SIMPLE}' )
      controller.write( f'-gdb-set new-console on' )
      controller.write( f'-file-exec-and-symbols {SIMPLE}/simple' )

      # Fails, because 'on' should not be there
      responses = controller.write( f'1001-break-insert -f main' )
      for response in responses:
        if response[ 'token' ] != '1001' or response[ 'type' ] != 'result':
          continue

        self.assertEqual( response[ 'message' ], 'done' )
        self.assertEqual( response[ 'payload' ][ 'bkpt' ][ 'file' ],
                          os.path.join( SIMPLE, 'simple' ) )
        self.assertEqual( response[ 'payload' ][ 'bkpt' ][ 'line' ], 15 )

      responses = controller.write( f'-exec-run' )

      found = False
      for i in range( 4 ):
        for response in responses:
          if ( response[ 'type' ] == 'notify' and
               response[ 'message' ] == 'stopped' ):
            found = True
            break

        if found:
          break

        responses = controller.get_gdb_response( raise_error_on_timeout=False )

      self.assertTrue( found )
      self.assertEqual( response[ 'message' ], 'stopped' )
      self.assertEqual( response[ 'payload' ][ 'reason' ], 'breakpoint-hit' )
      self.assertEqual( response[ 'payload' ][ 'frame' ][ 'func' ], 'main' )

      controller.write( '-exec-continue' )
    finally:
      controller.exit()



if __name__ == '__main__':
  unittest.main()
