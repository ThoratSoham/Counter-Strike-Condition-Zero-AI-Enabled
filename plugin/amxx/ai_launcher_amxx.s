	.text
	.globl	_DllMain@12
	.def	_DllMain@12;	.scl	2;	.type	32;	.endef
_DllMain@12:
	movl	$1, %eax
	ret	$12

	.globl	_AMXX_Query
	.def	_AMXX_Query;	.scl	2;	.type	32;	.endef
_AMXX_Query:
	pushl	%ebp
	movl	%esp, %ebp
	movl	8(%ebp), %eax
	testl	%eax, %eax
	je	L_query_param
	movl	12(%ebp), %ecx
	testl	%ecx, %ecx
	je	L_query_param
	cmpl	$4, (%eax)
	je	L_query_ok
	movl	$4, (%eax)
	movl	$1, %eax
	popl	%ebp
	ret
L_query_ok:
	movl	$_str_name, 0(%ecx)
	movl	$_str_author, 4(%ecx)
	movl	$_str_version, 8(%ecx)
	movl	$0, 12(%ecx)
	movl	$_str_logtag, 16(%ecx)
	movl	$_str_library, 20(%ecx)
	movl	$_str_libclass, 24(%ecx)
	xorl	%eax, %eax
	popl	%ebp
	ret
L_query_param:
	movl	$2, %eax
	popl	%ebp
	ret

	.globl	_AMXX_CheckGame
	.def	_AMXX_CheckGame;	.scl	2;	.type	32;	.endef
_AMXX_CheckGame:
	xorl	%eax, %eax
	ret

	.globl	_AMXX_Attach
	.def	_AMXX_Attach;	.scl	2;	.type	32;	.endef
_AMXX_Attach:
	pushl	$0
	pushl	$_str_cmdline
	call	_WinExec@8
	xorl	%eax, %eax
	ret

	.globl	_AMXX_Detach
	.def	_AMXX_Detach;	.scl	2;	.type	32;	.endef
_AMXX_Detach:
	xorl	%eax, %eax
	ret

	.globl	_AMXX_PluginsLoaded
	.def	_AMXX_PluginsLoaded;	.scl	2;	.type	32;	.endef
_AMXX_PluginsLoaded:
	xorl	%eax, %eax
	ret

	.globl	_AMXX_PluginsUnloaded
	.def	_AMXX_PluginsUnloaded;	.scl	2;	.type	32;	.endef
_AMXX_PluginsUnloaded:
	xorl	%eax, %eax
	ret

	.globl	_AMXX_PluginsUnloading
	.def	_AMXX_PluginsUnloading;	.scl	2;	.type	32;	.endef
_AMXX_PluginsUnloading:
	xorl	%eax, %eax
	ret

	.section .rdata,"dr"
_str_name:
	.asciz "AI Brain Auto-Launcher"
_str_author:
	.asciz "AI Teammates Mod"
_str_version:
	.asciz "1.0"
_str_logtag:
	.asciz "AILAUNCH"
_str_library:
	.asciz "ai_launcher"
_str_libclass:
	.asciz ""
_str_cmdline:
	.asciz "cmd.exe /c if exist \"main.py\" (start \"\" /b py main.py --no-ui) else (if exist \"..\\main.py\" cd /d .. && start \"\" /b py main.py --no-ui)"
